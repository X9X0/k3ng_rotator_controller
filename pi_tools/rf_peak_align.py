#!/usr/bin/env python3
"""
RF peak alignment for a K3NG-controlled dish, using an RTL-SDR as the signal meter.

Runs on the Pi at the dish. Sweeps the dish in a cross pattern (azimuth, then
elevation) around where a known beacon should be, measures signal-over-noise
at each stop, fits the peak, and reports how far the controller's idea of
az/el is from the truth. With --apply it tells the controller its true
position (\\A and \\B commands).

The usual beacon is a GOES satellite (geostationary, HRIT at 1694.1 MHz):

    ./rf_peak_align.py --port /dev/ttyACM0 --lat 40.0 --lon -100.0 --sat-lon -75.2

Dry run with no hardware (simulated dish with a hidden pointing error):

    ./rf_peak_align.py --simulate --lat 40.0 --lon -100.0 --sat-lon -75.2

Requires: numpy, pyserial, and the `rtl_sdr` command (package rtl-sdr).
"""

import argparse
import math
import re
import subprocess
import sys
import time

import numpy as np

GEO_RADIUS_RATIO = 6378.137 / 42164.0  # earth radius / geostationary orbit radius


def geo_look_angles(lat, lon, sat_lon):
    """Azimuth/elevation (degrees) to a geostationary satellite. East longitudes positive."""
    la, dl = math.radians(lat), math.radians(sat_lon - lon)
    az = math.degrees(math.atan2(math.sin(dl), -math.sin(la) * math.cos(dl))) % 360.0
    cosg = math.cos(la) * math.cos(dl)
    el = math.degrees(math.atan2(cosg - GEO_RADIUS_RATIO, math.sqrt(1.0 - cosg * cosg)))
    return az, el


def wrap180(deg):
    return (deg + 180.0) % 360.0 - 180.0


# ----------------------------------------------------------------------------
# Rotator (K3NG backslash commands over the control port)
# ----------------------------------------------------------------------------

class K3NGRotator:
    def __init__(self, port, baud, boot_wait):
        import serial
        self.ser = serial.Serial(port, baud, timeout=0.5)
        # Opening the port resets most Arduinos, and K3NG ignores rotation
        # commands for its first 10 seconds unless built to allow them.
        print(f"Waiting {boot_wait:.0f}s for the controller to boot...")
        time.sleep(boot_wait)
        self.ser.reset_input_buffer()

    def _command(self, cmd, pattern=None, timeout=3.0):
        self.ser.reset_input_buffer()
        self.ser.write((cmd + "\r").encode("ascii"))  # K3NG executes on carriage return
        deadline = time.time() + timeout
        last = ""
        while time.time() < deadline:
            line = self.ser.readline().decode("ascii", errors="replace").strip()
            if not line:
                continue
            last = line
            if pattern is None:
                return line
            m = re.search(pattern, line)
            if m:
                return m
        if pattern is None:
            return last
        raise RuntimeError(f"No valid reply to {cmd!r} (last line: {last!r})")

    def position(self):
        az = float(self._command("\\?AZ", r"(\d+\.\d+)\s*$").group(1))
        m = self._command("\\?EL", r"([+-]?)(\d+\.\d+)\s*$")
        el = float(m.group(2)) * (-1.0 if m.group(1) == "-" else 1.0)
        return az, el

    def goto(self, az, el):
        self._command(f"\\?GA{az % 360.0:05.1f}")
        self._command(f"\\?GE{el:05.1f}")

    def set_true_position(self, az, el):
        # Whole degrees: the encoder/pulse-input builds only parse integers.
        print("  ", self._command(f"\\A{int(round(az)) % 360}"))
        print("  ", self._command(f"\\B{int(round(el))}"))

    def stop(self):
        try:
            self._command("\\?SS", timeout=1.0)
        except Exception:
            pass


class RtlSdrMeter:
    """In-band power over out-of-band noise, in dB. Insensitive to receiver gain drift."""

    def __init__(self, freq, gain, ppm, rate, signal_bw, seconds, bias_tee=False):
        self.freq, self.gain, self.ppm, self.rate = freq, gain, ppm, rate
        self.bias_tee = bias_tee
        self.signal_bw, self.seconds = signal_bw, seconds

    def measure(self):
        settle = int(0.2 * self.rate)
        n = int(self.seconds * self.rate) + settle
        cmd = ["rtl_sdr", "-f", str(int(self.freq)), "-s", str(int(self.rate)),
               "-g", str(self.gain), "-p", str(self.ppm), "-n", str(n)]
        if self.bias_tee:
            cmd.append("-T")  # power an LNA at the feed from the dongle's bias tee
        cmd.append("-")
        out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        raw = np.frombuffer(out.stdout, dtype=np.uint8)[2 * settle:]
        if raw.size < 2 * 65536:
            raise RuntimeError("rtl_sdr returned too little data:\n" + out.stderr.decode(errors="replace"))
        return band_ratio_db(raw, self.rate, self.signal_bw)


def band_ratio_db(raw_iq_u8, rate, signal_bw, nfft=4096):
    iq = (raw_iq_u8.astype(np.float32) - 127.5) / 127.5
    x = iq[0::2] + 1j * iq[1::2]
    segs = x[: (x.size // nfft) * nfft].reshape(-1, nfft) * np.hanning(nfft)
    psd = np.fft.fftshift(np.mean(np.abs(np.fft.fft(segs, axis=1)) ** 2, axis=0))
    f = np.abs(np.fft.fftshift(np.fft.fftfreq(nfft, 1.0 / rate)))
    nyq = rate / 2.0
    inband = (f > 15e3) & (f < signal_bw / 2.0)          # skip the DC spike
    noise = (f > 0.72 * nyq) & (f < 0.88 * nyq)          # past the signal, before filter roll-off
    if signal_bw / 2.0 > 0.7 * nyq:
        raise ValueError("--signal-bw is too wide for the sample rate to leave a noise reference")
    return 10.0 * math.log10(psd[inband].mean() / psd[noise].mean())


# ----------------------------------------------------------------------------
# Simulation: a dish whose reported position is wrong by a hidden error
# ----------------------------------------------------------------------------

class Simulation:
    def __init__(self, beacon_az, beacon_el, az_err, el_err, beamwidth, peak_db):
        self.beacon = (beacon_az, beacon_el)
        self.err = (az_err, el_err)            # reported minus true
        self.bw, self.peak_db = beamwidth, peak_db
        self.rep = [beacon_az - 30.0, 20.0]
        self.rng = np.random.default_rng(1)

    def position(self):
        return self.rep[0] % 360.0, self.rep[1]

    def goto(self, az, el):
        # mimic the firmware stopping anywhere inside its tolerance band
        self.rep = [az + self.rng.uniform(-0.8, 0.8), el + self.rng.uniform(-0.3, 0.3)]

    def set_true_position(self, az, el):
        t_az, t_el = self.rep[0] - self.err[0], self.rep[1] - self.err[1]
        print(f"   [sim] controller told {int(round(az)) % 360}/{int(round(el))}, "
              f"dish truly at {t_az % 360:.1f}/{t_el:.1f}")

    def stop(self):
        pass

    def measure(self):
        a1, e1 = math.radians(self.rep[0] - self.err[0]), math.radians(self.rep[1] - self.err[1])
        a2, e2 = math.radians(self.beacon[0]), math.radians(self.beacon[1])
        c = math.sin(e1) * math.sin(e2) + math.cos(e1) * math.cos(e2) * math.cos(a1 - a2)
        sep = math.degrees(math.acos(max(-1.0, min(1.0, c))))
        snr = 10 ** (self.peak_db / 10.0) - 1.0
        gain = math.exp(-4.0 * math.log(2.0) * (sep / self.bw) ** 2)
        return 10.0 * math.log10(1.0 + snr * gain) + self.rng.normal(0, 0.05)


# ----------------------------------------------------------------------------
# Scan and fit
# ----------------------------------------------------------------------------

def move_and_settle(rot, az, el, timeout, simulate):
    rot.goto(az, el)
    if simulate:
        return rot.position()
    deadline = time.time() + timeout
    last, steady = None, 0
    time.sleep(1.0)
    while time.time() < deadline:
        pos = rot.position()
        if last and abs(wrap180(pos[0] - last[0])) < 0.05 and abs(pos[1] - last[1]) < 0.05:
            steady += 1
            if steady >= 3:
                return pos
        else:
            steady = 0
        last = pos
        time.sleep(0.5)
    raise RuntimeError(f"Dish did not settle at az {az:.1f} el {el:.1f} within {timeout:.0f}s")


def fit_peak(xs, dbs, min_contrast):
    """Quadratic fit through the top of the sweep. Returns (peak_x, peak_db) or raises."""
    xs, dbs = np.asarray(xs), np.asarray(dbs)
    floor = np.median(np.sort(dbs)[: max(2, len(dbs) // 4)])
    contrast = dbs.max() - floor
    if contrast < min_contrast:
        raise RuntimeError(f"no clear peak: only {contrast:.2f} dB between best and worst points")
    top = dbs >= dbs.max() - max(1.0, 0.5 * contrast)
    if top.sum() < 3:  # widen to the best point and its neighbours
        i = int(np.argmax(dbs))
        top = np.zeros(len(dbs), bool)
        top[max(0, i - 1): i + 2] = True
    if top.sum() < 3:
        raise RuntimeError("peak is at the edge of the sweep; widen --span or fix coarse pointing")
    a, b, c = np.polyfit(xs[top], dbs[top], 2)
    if a >= 0:
        raise RuntimeError("points near the maximum do not form a peak")
    x0 = -b / (2 * a)
    if not xs.min() < x0 < xs.max():
        raise RuntimeError("peak is at the edge of the sweep; widen --span or fix coarse pointing")
    return float(x0), float(np.polyval([a, b, c], x0))


def sweep(rot, meter, axis, centre_az, centre_el, offsets, args):
    """Sweep one axis. Returns reported positions (relative to centre) and dB readings."""
    xs, dbs = [], []
    for off in offsets:
        az = centre_az + off if axis == "az" else centre_az
        el = centre_el if axis == "az" else centre_el + off
        if not args.el_min <= el <= args.el_max:
            continue
        r_az, r_el = move_and_settle(rot, az, el, args.move_timeout, args.simulate)
        db = meter.measure()
        x = wrap180(r_az - centre_az) if axis == "az" else r_el - centre_el
        xs.append(x)
        dbs.append(db)
        print(f"  {axis} {r_az:7.2f}  el {r_el:6.2f}   {db:6.2f} dB  " + "#" * max(0, int(round(db * 4))))
    if len(xs) < 5:
        raise RuntimeError(f"only {len(xs)} usable points in the {axis} sweep (check --el-min/--el-max)")
    return xs, dbs


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    tgt = p.add_argument_group("beacon position (give az/el directly, or a site and satellite longitude)")
    tgt.add_argument("--az", type=float, help="true azimuth of the beacon, degrees")
    tgt.add_argument("--el", type=float, help="true elevation of the beacon, degrees")
    tgt.add_argument("--lat", type=float, help="site latitude, degrees north")
    tgt.add_argument("--lon", type=float, help="site longitude, degrees east (west is negative)")
    tgt.add_argument("--sat-lon", type=float, help="geostationary satellite longitude, degrees east "
                                                   "(GOES-East -75.2, GOES-West -137.0)")
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--boot-wait", type=float, default=12.0, help="seconds to wait after opening the port")
    p.add_argument("--freq", type=float, default=1694.1e6, help="beacon centre frequency, Hz (default GOES HRIT)")
    p.add_argument("--signal-bw", type=float, default=1.0e6, help="occupied bandwidth of the beacon, Hz")
    p.add_argument("--rate", type=float, default=2.4e6, help="SDR sample rate")
    p.add_argument("--gain", type=float, default=40.0, help="fixed tuner gain, dB (never automatic)")
    p.add_argument("--ppm", type=int, default=0)
    p.add_argument("--bias-tee", action="store_true", help="turn on the dongle's bias tee to power the LNA")
    p.add_argument("--dwell", type=float, default=1.0, help="seconds of samples per point")
    p.add_argument("--span", type=float, default=20.0, help="sweep half-width on the sky, degrees")
    p.add_argument("--step", type=float, default=2.5, help="sweep step on the sky, degrees")
    p.add_argument("--el-min", type=float, default=5.0)
    p.add_argument("--el-max", type=float, default=85.0)
    p.add_argument("--min-contrast", type=float, default=1.0, help="dB the peak must stand above the sweep floor")
    p.add_argument("--move-timeout", type=float, default=120.0)
    p.add_argument("--apply", action="store_true", help="write the corrected position to the controller")
    p.add_argument("--simulate", action="store_true", help="no hardware; simulated dish with a hidden error")
    args = p.parse_args()

    if args.az is not None and args.el is not None:
        az0, el0 = args.az % 360.0, args.el
    elif None not in (args.lat, args.lon, args.sat_lon):
        az0, el0 = geo_look_angles(args.lat, args.lon, args.sat_lon)
    else:
        p.error("give either --az and --el, or --lat, --lon and --sat-lon")
    if not args.el_min <= el0 <= args.el_max:
        sys.exit(f"Beacon elevation {el0:.1f} is outside the dish limits {args.el_min}-{args.el_max}.")
    print(f"Beacon expected at az {az0:.1f}, el {el0:.1f}")

    if args.simulate:
        rot = meter = Simulation(az0, el0, az_err=7.3, el_err=-3.1, beamwidth=20.0, peak_db=4.0)
    else:
        rot = K3NGRotator(args.port, args.baud, args.boot_wait)
        meter = RtlSdrMeter(args.freq, args.gain, args.ppm, args.rate, args.signal_bw, args.dwell, args.bias_tee)

    offsets = np.arange(-args.span, args.span + 1e-6, args.step)
    # An azimuth step moves the beam less on the sky the higher the dish points.
    az_stretch = min(1.0 / math.cos(math.radians(el0)), 4.0)
    try:
        print("\nAzimuth sweep")
        xs, dbs = sweep(rot, meter, "az", az0, el0, offsets * az_stretch, args)
        az_off, _ = fit_peak(xs, dbs, args.min_contrast)

        print("\nElevation sweep")
        xs, dbs = sweep(rot, meter, "el", az0 + az_off, el0, offsets, args)
        el_off, _ = fit_peak(xs, dbs, args.min_contrast)

        print("\nAzimuth sweep (refine at peak elevation)")
        xs, dbs = sweep(rot, meter, "az", az0 + az_off, el0 + el_off, offsets * az_stretch / 2.0, args)
        az_fine, peak_db = fit_peak(xs, dbs, args.min_contrast)
        az_off += az_fine

        print(f"\nPeak {peak_db:.2f} dB at reported az {(az0 + az_off) % 360:.1f}, el {el0 + el_off:.1f}")
        print(f"Controller error (reported minus true): azimuth {az_off:+.1f} deg, elevation {el_off:+.1f} deg.")

        if args.apply:
            r_az, r_el = move_and_settle(rot, az0 + az_off, el0 + el_off, args.move_timeout, args.simulate)
            true_az = az0 + wrap180(r_az - (az0 + az_off))
            true_el = el0 + (r_el - (el0 + el_off))
            print("Writing corrected position to the controller:")
            rot.set_true_position(true_az, true_el)
        else:
            print("Nothing written to the controller (run again with --apply to correct it).")
    except KeyboardInterrupt:
        rot.stop()
        sys.exit("\nInterrupted; rotation stopped.")
    except RuntimeError as e:
        rot.stop()
        sys.exit(f"\nAlignment failed: {e}")


if __name__ == "__main__":
    main()
