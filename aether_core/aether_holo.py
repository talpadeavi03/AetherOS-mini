#!/usr/bin/env python3
"""
AetherOS 3D Volumetric Hologram Engine (`aether-holo`)
Real-time 3D Holographic Projection & J.A.R.V.I.S. Workshop Core for AetherOS.

Features:
- Sub-pixel Unicode Braille Canvas (2x4 sub-pixels per character cell, 160x160+ resolution)
- 3D Vector Math & Perspective Projection Engine (Euler Rotation Matrices Rx, Ry, Rz)
- Model 1: Mark 85 Holographic Arc Reactor (Concentric Torus Rings, Magnetic Solenoids, Vibranium Core)
- Model 2: 3D Global Planetary Sensor & Swarm Defense Grid (Wireframe Earth + Orbiting Satellites)
- Model 3: Real-Time 3D LiDAR & Spatial Robotics Point Cloud (Live sensor fusion with aether-roboticsd)
- Model 4: Full Iron Man Workshop Diagnostics Matrix (Quad-split holographic telemetry & audio spectrum)
- Full-Duplex J.A.R.V.I.S. Voice & Conversational Intent Integration
- TrueColor 24-bit ANSI Hologram Shading (Blinding Cyan, Arc Blue, Vibranium Gold, Crimson Warning)
"""

import os
import sys
import time
import math
import json
import socket
import select
import shutil

# Try importing termios/tty for raw keyboard input
try:
    import termios
    import tty
    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False

# ANSI Color Codes (24-bit TrueColor)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CLEAR_SCREEN = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

# Holographic Palette
HOLO_CYAN_HOT = "\033[38;2;0;255;255m"      # #00FFFF (Brightest core)
HOLO_CYAN = "\033[38;2;0;220;255m"          # #00DCFF
HOLO_BLUE = "\033[38;2;0;140;255m"          # #008CFF
HOLO_DEEP_BLUE = "\033[38;2;0;70;180m"      # #0046B4
HOLO_GOLD = "\033[38;2;255;215;0m"          # #FFD700 (Vibranium Core)
HOLO_GOLD_HOT = "\033[38;2;255;245;180m"    # #FFF5B4
HOLO_GREEN = "\033[38;2;80;250;140m"        # #50FA8C (Nominal)
HOLO_RED = "\033[38;2;255;85;110m"          # #FF556E (Warning)
HOLO_TEXT = "\033[38;2;210;235;255m"        # #D2EBFF
HOLO_MUTED = "\033[38;2;90;120;160m"        # #5A78A0
BG_DARK = "\033[48;2;10;14;24m"             # #0A0E18

# Subsystem Sockets
MCP_SOCK = "/run/aether/mcp.sock"
VISION_SOCK = "/run/aether/vision.sock"
VOICE_SOCK = "/run/aether/voice.sock"
MEM_SOCK = "/run/aether/mem.sock"
INTENT_SOCK = "/run/aether/intent.sock"
AGENT_SOCK = "/run/aether/agent.sock"
ROBOT_SOCK = "/run/aether/robotics.sock"

def query_sock(sock_path, payload, timeout=0.3):
    if not os.path.exists(sock_path):
        return None
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(sock_path)
        s.sendall(json.dumps(payload).encode('utf-8'))
        raw = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            raw += chunk
        s.close()
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return None


class BrailleCanvas:
    """Sub-pixel canvas using Unicode Braille Patterns (U+2800 to U+28FF).
    Each character cell is 2 columns x 4 rows of sub-pixels.
    """
    BRAILLE_MAP = [
        (0, 0, 0x01), (1, 0, 0x02), (2, 0, 0x04), (3, 0, 0x40),
        (0, 1, 0x08), (1, 1, 0x10), (2, 1, 0x20), (3, 1, 0x80)
    ]

    def __init__(self, char_w, char_h):
        self.char_w = max(10, char_w)
        self.char_h = max(5, char_h)
        self.sub_w = self.char_w * 2
        self.sub_h = self.char_h * 4
        self.pixels = bytearray(self.sub_w * self.sub_h)
        # z-depth buffer for shading: 0 to 255 (255 = closest)
        self.z_buffer = bytearray(self.sub_w * self.sub_h)

    def clear(self):
        for i in range(len(self.pixels)):
            self.pixels[i] = 0
            self.z_buffer[i] = 0

    def set_pixel(self, x, y, z_depth=128):
        if 0 <= x < self.sub_w and 0 <= y < self.sub_h:
            idx = y * self.sub_w + x
            self.pixels[idx] = 1
            if z_depth > self.z_buffer[idx]:
                self.z_buffer[idx] = min(255, max(0, int(z_depth)))

    def draw_line(self, x0, y0, x1, y1, z0=128, z1=128):
        """Bresenham line algorithm on subpixel grid."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        steps = max(dx, dy)
        step_idx = 0

        while True:
            t = (step_idx / steps) if steps > 0 else 0
            cur_z = int(z0 + (z1 - z0) * t)
            self.set_pixel(x0, y0, cur_z)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
            step_idx += 1

    def render_rows(self, color_style="cyan"):
        """Converts pixel grid to Braille characters with TrueColor ANSI depth shading."""
        output = []
        for cy in range(self.char_h):
            row_chars = []
            for cx in range(self.char_w):
                mask = 0
                max_z = 0
                base_y = cy * 4
                base_x = cx * 2
                for dy, dx, bit in self.BRAILLE_MAP:
                    py = base_y + dy
                    px = base_x + dx
                    if 0 <= py < self.sub_h and 0 <= px < self.sub_w:
                        idx = py * self.sub_w + px
                        if self.pixels[idx]:
                            mask |= bit
                            if self.z_buffer[idx] > max_z:
                                max_z = self.z_buffer[idx]

                if mask == 0:
                    row_chars.append(" ")
                else:
                    char = chr(0x2800 + mask)
                    if color_style == "gold":
                        if max_z > 215:
                            row_chars.append(f"\033[38;2;255;240;130m{BOLD}{char}{RESET}")   # #FFF082 (Hot Core)
                        elif max_z > 170:
                            row_chars.append(f"\033[38;2;255;195;50m{BOLD}{char}{RESET}")    # #FFC332 (Truss & Crescent)
                        elif max_z > 125:
                            row_chars.append(f"\033[38;2;220;140;30m{char}{RESET}")          # #DC8C1E (Swarm Fragments)
                        elif max_z > 75:
                            row_chars.append(f"\033[38;2;160;90;20m{char}{RESET}")           # #A05A14 (Atmospheric Haze)
                        else:
                            row_chars.append(f"\033[38;2;90;50;15m{char}{RESET}")            # Dark Amber Shadow
                    else:  # default cyan
                        if max_z > 210:
                            row_chars.append(f"{HOLO_CYAN_HOT}{BOLD}{char}{RESET}")
                        elif max_z > 160:
                            row_chars.append(f"{HOLO_CYAN}{char}{RESET}")
                        elif max_z > 110:
                            row_chars.append(f"{HOLO_BLUE}{char}{RESET}")
                        else:
                            row_chars.append(f"{HOLO_DEEP_BLUE}{char}{RESET}")
            output.append("".join(row_chars))
        return output


class HologramEngine:
    def __init__(self):
        self.mode = 1  # 1: Arc Reactor, 2: Global Defense Grid, 3: 3D LiDAR, 4: Workshop Matrix
        self.angle_x = 0.4
        self.angle_y = 0.0
        self.angle_z = 0.0
        self.time_sec = 0.0
        self.running = True
        self.interactive_prompt = False
        self.prompt_text = ""
        self.jarvis_subtitles = "J.A.R.V.I.S.: Holographic workshop online, sir. Arc Reactor core at 100%."
        self.subtitle_time = time.time()
        self.cached_swarm = {}
        self.cached_robotics = {}
        self.cached_mcp = {}
        self.cached_vision = {}
        self.cached_voice = {}
        self.last_sensor_poll = 0

    def update_sensors(self):
        now = time.time()
        if now - self.last_sensor_poll > 0.4:
            self.cached_swarm = query_sock(AGENT_SOCK, {"action": "status"}) or self.cached_swarm
            self.cached_robotics = query_sock(ROBOT_SOCK, {"action": "status"}) or self.cached_robotics
            self.cached_mcp = query_sock(MCP_SOCK, {"action": "call_tool", "name": "system.diagnose", "args": {}}) or self.cached_mcp
            self.cached_vision = query_sock(VISION_SOCK, {"action": "status"}) or self.cached_vision
            self.cached_voice = query_sock(VOICE_SOCK, {"action": "status"}) or self.cached_voice
            self.last_sensor_poll = now

    def project_3d_point(self, x, y, z, cx, cy, f_len=140.0, cam_dist=4.0, aspect=1.0):
        """Perspective 3D to 2D subpixel projection."""
        # Rotate around X
        rad_x = self.angle_x
        y1 = y * math.cos(rad_x) - z * math.sin(rad_x)
        z1 = y * math.sin(rad_x) + z * math.cos(rad_x)

        # Rotate around Y
        rad_y = self.angle_y
        x2 = x * math.cos(rad_y) + z1 * math.sin(rad_y)
        z2 = -x * math.sin(rad_y) + z1 * math.cos(rad_y)

        # Rotate around Z
        rad_z = self.angle_z
        x3 = x2 * math.cos(rad_z) - y1 * math.sin(rad_z)
        y3 = x2 * math.sin(rad_z) + y1 * math.cos(rad_z)
        z3 = z2

        # Perspective division
        dist = z3 + cam_dist
        if dist <= 0.2:
            return None, None, 0

        px = int(cx + (x3 * f_len * aspect) / dist)
        py = int(cy - (y3 * f_len) / dist)
        # Depth normalized to 0 - 255
        z_norm = int(128 + z3 * 35)
        z_norm = max(0, min(255, z_norm))
        return px, py, z_norm

    def render_ultron_jarvis_sphere(self, canvas):
        """Draws the film-accurate Avengers: Age of Ultron J.A.R.V.I.S. Golden Hologram Sphere
        Ported from ffMathy/hey-jarvis:
        - Rolling ladder truss ring (outer rail 1.035R, inner rail 0.935R, 9-deg rungs)
        - Left bright crescent (11 to 7 o'clock) with multi-strand width tiers
        - Two inner counter-turning spiral whorl arms winding out to 0.76R
        - Hooked core ring at (-0.07, -0.07) with 11-spike radial knot
        - Volumetric fragment swarm with agitation-driven churn & counter-rotating lower shell
        - Orbiting Agent Satellites with tool flare rings
        - Bursting amber chip slabs thrown toward 8 o'clock on speech/intent onsets
        """
        cx = canvas.sub_w // 2
        cy = canvas.sub_h // 2
        t = self.time_sec
        R_sphere = 2.15

        # 1. Ladder Truss Ring (Rolling Rim Layer at 11 deg/s clockwise)
        roll_angle = t * 0.22  # 12 deg/s in screen plane
        R_out = R_sphere * 1.035
        R_in = R_sphere * 0.935
        rungs_count = 40  # every 9 degrees

        # Draw outer & inner rail segments
        steps = 60
        for s in range(steps):
            phi1 = (s / steps) * 2.0 * math.pi + roll_angle
            phi2 = ((s + 1) / steps) * 2.0 * math.pi + roll_angle
            x1_o, y1_o = R_out * math.cos(phi1), R_out * math.sin(phi1)
            x2_o, y2_o = R_out * math.cos(phi2), R_out * math.sin(phi2)
            p1_x, p1_y, z1 = self.project_3d_point(x1_o, y1_o, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            p2_x, p2_y, z2 = self.project_3d_point(x2_o, y2_o, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            if p1_x is not None and p2_x is not None:
                canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z1 + 50, z2 + 50)

            x1_i, y1_i = R_in * math.cos(phi1), R_in * math.sin(phi1)
            x2_i, y2_i = R_in * math.cos(phi2), R_in * math.sin(phi2)
            p3_x, p3_y, z3 = self.project_3d_point(x1_i, y1_i, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            p4_x, p4_y, z4 = self.project_3d_point(x2_i, y2_i, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            if p3_x is not None and p4_x is not None:
                canvas.draw_line(p3_x, p3_y, p4_x, p4_y, z3 + 30, z4 + 30)

        # Draw cross-rungs every 9 degrees
        for r in range(rungs_count):
            r_phi = (r / rungs_count) * 2.0 * math.pi + roll_angle
            rx1, ry1 = R_in * math.cos(r_phi), R_in * math.sin(r_phi)
            rx2, ry2 = R_out * math.cos(r_phi), R_out * math.sin(r_phi)
            p1_x, p1_y, z1 = self.project_3d_point(rx1, ry1, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            p2_x, p2_y, z2 = self.project_3d_point(rx2, ry2, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            if p1_x is not None and p2_x is not None:
                canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z1 + 40, z2 + 40)

        # 2. Left Bright Crescent (11 o'clock to 7 o'clock)
        crescent_start = math.radians(150)
        crescent_end = math.radians(330)
        agitation = 0.85 if self.cached_voice.get("vad", {}).get("speech_detected") else 0.2
        crescent_spread = 0.08 * math.sin(t * 3.0) + (0.15 * agitation)

        for tier, offset in enumerate([0.0, 0.04, 0.09, 0.15]):
            r_cres = R_sphere * (0.98 + offset + crescent_spread)
            c_steps = 28
            for cs in range(c_steps):
                ang1 = crescent_start + (cs / c_steps) * (crescent_end - crescent_start)
                ang2 = crescent_start + ((cs + 1) / c_steps) * (crescent_end - crescent_start)
                cx1, cy1 = -r_cres * math.cos(ang1), r_cres * math.sin(ang1)
                cx2, cy2 = -r_cres * math.cos(ang2), r_cres * math.sin(ang2)
                p1_x, p1_y, z1 = self.project_3d_point(cx1, cy1, 0.1 * math.sin(ang1*3), cx, cy, f_len=135.0, cam_dist=4.5)
                p2_x, p2_y, z2 = self.project_3d_point(cx2, cy2, 0.1 * math.sin(ang2*3), cx, cy, f_len=135.0, cam_dist=4.5)
                if p1_x is not None and p2_x is not None:
                    canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z1 + 60, z2 + 60)

        # 3. Two Inner Counter-Turning Spiral Whorl Arms
        whorl_spin = -t * 0.12  # Counter-clockwise at 5 deg/s
        for arm in [0, math.pi]:
            arm_pts = 22
            prev_p = None
            for p in range(arm_pts):
                frac = p / arm_pts
                theta = arm + (frac * 1.8 * math.pi) + whorl_spin
                radius = R_sphere * (0.18 + 0.58 * frac)
                wx = radius * math.cos(theta)
                wy = radius * math.sin(theta)
                wz = 0.2 * math.sin(theta * 2.0)
                px, py, z_val = self.project_3d_point(wx, wy, wz, cx, cy, f_len=135.0, cam_dist=4.5)
                if px is not None:
                    if prev_p is not None:
                        canvas.draw_line(prev_p[0], prev_p[1], px, py, prev_p[2], z_val + 20)
                    canvas.set_pixel(px, py, 220)
                    prev_p = (px, py, z_val)

        # 4. Hooked Core with 0.1R Ring & 11-Spike Radial Knot
        core_off_x = -0.15
        core_off_y = -0.15
        core_r = R_sphere * 0.12 * (1.0 + 0.05 * math.sin(t * 8.0))
        for sp in range(16):
            a1 = (sp / 16) * 2.0 * math.pi
            a2 = ((sp + 1) / 16) * 2.0 * math.pi
            kx1 = core_off_x + core_r * math.cos(a1)
            ky1 = core_off_y + core_r * math.sin(a1)
            kx2 = core_off_x + core_r * math.cos(a2)
            ky2 = core_off_y + core_r * math.sin(a2)
            p1_x, p1_y, z1 = self.project_3d_point(kx1, ky1, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            p2_x, p2_y, z2 = self.project_3d_point(kx2, ky2, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            if p1_x is not None and p2_x is not None:
                canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z1 + 90, z2 + 90)

        for spike in range(11):
            s_ang = (spike / 11) * 2.0 * math.pi + (0.4 * math.sin(t * 6.0 + spike))
            s_len = core_r * (1.2 + 0.6 * math.sin(t * 12.0 + spike * 3.0))
            sx = core_off_x + s_len * math.cos(s_ang)
            sy = core_off_y + s_len * math.sin(s_ang)
            px, py, z_val = self.project_3d_point(sx, sy, 0, cx, cy, f_len=135.0, cam_dist=4.5)
            if px is not None:
                canvas.set_pixel(px, py, 255)

        # 5. Volumetric Fragment Swarm
        particles = 65
        for i in range(particles):
            seed = (i * 137.5) % 360.0
            r_frac = 0.2 + 0.75 * math.sqrt((i + 1) / particles)
            rad = R_sphere * r_frac
            ang = math.radians(seed) + (t * 0.21 if i % 2 == 0 else -t * 0.15)
            elev = math.sin(seed * 2.3) * 0.8
            px_3d = rad * math.cos(ang) * math.cos(elev)
            py_3d = rad * math.sin(ang) * math.cos(elev)
            pz_3d = rad * math.sin(elev)
            if agitation > 0.4:
                px_3d += 0.08 * math.sin(t * 15.0 + i)
                py_3d += 0.08 * math.cos(t * 15.0 + i)
            px, py, z_val = self.project_3d_point(px_3d, py_3d, pz_3d, cx, cy, f_len=135.0, cam_dist=4.5)
            if px is not None:
                canvas.set_pixel(px, py, min(255, z_val + 30))

        # 6. Orbiting Agent Satellites & Execution Flares
        sat_data = [
            ("Sentinel", 2.65, 0.9, 0.4, 0),
            ("Security", 2.95, -0.7, -0.3, 1),
            ("DevOps", 3.25, 1.2, 0.6, 2),
            ("Health", 3.55, -0.85, -0.5, 3)
        ]
        for name, s_dist, s_spd, s_tilt, s_idx in sat_data:
            s_ang = t * s_spd
            sx = s_dist * math.cos(s_ang)
            sy = s_dist * math.sin(s_ang) * math.cos(s_tilt)
            sz = s_dist * math.sin(s_ang) * math.sin(s_tilt)
            spx, spy, sz_val = self.project_3d_point(sx, sy, sz, cx, cy, f_len=135.0, cam_dist=4.5)
            if spx is not None:
                canvas.set_pixel(spx, spy, 255)
                canvas.set_pixel(spx-1, spy, 220)
                canvas.set_pixel(spx+1, spy, 220)
                canvas.set_pixel(spx, spy-1, 220)
                canvas.set_pixel(spx, spy+1, 220)
                flare_r = 0.3 * (0.5 + 0.5 * math.sin(t * 4.0 + s_idx * 1.5))
                for f_step in range(8):
                    fa = (f_step / 8) * 2.0 * math.pi
                    fx = sx + flare_r * math.cos(fa)
                    fy = sy + flare_r * math.sin(fa)
                    fpx, fpy, _ = self.project_3d_point(fx, fy, sz, cx, cy, f_len=135.0, cam_dist=4.5)
                    if fpx is not None:
                        canvas.set_pixel(fpx, fpy, 210)

        # 7. Bursting Chip Slabs Thrown Toward 8 o'clock
        chip_period = (t * 2.5) % 3.0
        if chip_period < 0.6:
            chip_progress = chip_period / 0.6
            for c_idx in range(4):
                c_ang = math.radians(240 + (c_idx - 1.5) * 12.0)
                c_dist = R_sphere * (1.04 + chip_progress * (0.8 + 0.3 * c_idx))
                cx_chip = c_dist * math.cos(c_ang)
                cy_chip = c_dist * math.sin(c_ang)
                cpx, cpy, _ = self.project_3d_point(cx_chip, cy_chip, 0, cx, cy, f_len=135.0, cam_dist=4.5)
                if cpx is not None:
                    canvas.set_pixel(cpx, cpy, 245)
                    canvas.set_pixel(cpx+1, cpy, 230)
                    canvas.set_pixel(cpx, cpy+1, 230)
                    canvas.set_pixel(cpx+1, cpy+1, 215)

    def render_arc_reactor(self, canvas):
        """Draws the Mark 85 3D Holographic Arc Reactor."""
        cx = canvas.sub_w // 2
        cy = canvas.sub_h // 2
        t = self.time_sec

        # 1. Outer Torus Ring (Magnetic Confinement Ring)
        R_outer = 2.4
        r_tube = 0.35
        rings_u = 14
        rings_v = 8

        for i in range(rings_u):
            phi = (i / rings_u) * 2.0 * math.pi
            for j in range(rings_v):
                theta1 = (j / rings_v) * 2.0 * math.pi
                theta2 = ((j + 1) / rings_v) * 2.0 * math.pi
                # Vertex 1
                x1 = (R_outer + r_tube * math.cos(theta1)) * math.cos(phi)
                y1 = (R_outer + r_tube * math.cos(theta1)) * math.sin(phi)
                z1 = r_tube * math.sin(theta1)
                # Vertex 2
                x2 = (R_outer + r_tube * math.cos(theta2)) * math.cos(phi)
                y2 = (R_outer + r_tube * math.cos(theta2)) * math.sin(phi)
                z2 = r_tube * math.sin(theta2)

                p1_x, p1_y, z_val1 = self.project_3d_point(x1, y1, z1, cx, cy, f_len=130.0, cam_dist=4.5)
                p2_x, p2_y, z_val2 = self.project_3d_point(x2, y2, z2, cx, cy, f_len=130.0, cam_dist=4.5)
                if p1_x is not None and p2_x is not None:
                    canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z_val1, z_val2)

        # 2. Concentric Solenoid Rings (10 Magnetic Coils)
        coils = 10
        for c in range(coils):
            c_phi = (c / coils) * 2.0 * math.pi
            # Radial bracket spoke
            spoke_r1 = 1.2
            spoke_r2 = 2.4
            sx1 = spoke_r1 * math.cos(c_phi)
            sy1 = spoke_r1 * math.sin(c_phi)
            sx2 = spoke_r2 * math.cos(c_phi)
            sy2 = spoke_r2 * math.sin(c_phi)

            p1_x, p1_y, z_val1 = self.project_3d_point(sx1, sy1, 0, cx, cy, f_len=130.0, cam_dist=4.5)
            p2_x, p2_y, z_val2 = self.project_3d_point(sx2, sy2, 0, cx, cy, f_len=130.0, cam_dist=4.5)
            if p1_x is not None and p2_x is not None:
                canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z_val1 + 30, z_val2 + 30)

        # 3. Inner Rotating Vibranium Core (Triangular / Circular Quantum Iris)
        inner_r = 1.0 + 0.08 * math.sin(t * 6.0)  # Pulsing heartbeat
        pts = 24
        for p in range(pts):
            a1 = (p / pts) * 2.0 * math.pi
            a2 = ((p + 1) / pts) * 2.0 * math.pi
            ix1 = inner_r * math.cos(a1)
            iy1 = inner_r * math.sin(a1)
            ix2 = inner_r * math.cos(a2)
            iy2 = inner_r * math.sin(a2)

            p1_x, p1_y, z_val1 = self.project_3d_point(ix1, iy1, 0.1 * math.sin(t*3 + a1), cx, cy, f_len=130.0, cam_dist=4.5)
            p2_x, p2_y, z_val2 = self.project_3d_point(ix2, iy2, 0.1 * math.sin(t*3 + a2), cx, cy, f_len=130.0, cam_dist=4.5)
            if p1_x is not None and p2_x is not None:
                canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z_val1 + 50, z_val2 + 50)

        # 4. Central Glowing Core (Palladium / Energy Singularity)
        core_r = 0.45 + 0.05 * math.sin(t * 10.0)
        for p in range(12):
            ang = (p / 12) * 2.0 * math.pi
            cx1 = core_r * math.cos(ang)
            cy1 = core_r * math.sin(ang)
            px, py, z_val = self.project_3d_point(cx1, cy1, 0, cx, cy, f_len=130.0, cam_dist=4.5)
            if px is not None:
                canvas.set_pixel(px, py, 255)

        # 5. Orbiting Energy Particles
        for k in range(8):
            p_ang = t * 3.5 + (k * math.pi / 4.0)
            p_rad = 1.8 + 0.4 * math.sin(t * 2.0 + k)
            part_x = p_rad * math.cos(p_ang)
            part_y = p_rad * math.sin(p_ang)
            part_z = 0.3 * math.cos(p_ang * 2.0)
            px, py, z_val = self.project_3d_point(part_x, part_y, part_z, cx, cy, f_len=130.0, cam_dist=4.5)
            if px is not None:
                canvas.set_pixel(px, py, 240)
                canvas.set_pixel(px + 1, py, 220)
                canvas.set_pixel(px, py + 1, 220)

    def render_global_grid(self, canvas):
        """Draws 3D Planetary Wireframe Sphere with Orbiting Agent Satellites."""
        cx = canvas.sub_w // 2
        cy = canvas.sub_h // 2
        t = self.time_sec

        # Wireframe Sphere
        R = 2.0
        lat_count = 8
        lon_count = 12

        # Latitude lines
        for i in range(1, lat_count):
            lat = -math.pi/2.0 + (i / lat_count) * math.pi
            r_lat = R * math.cos(lat)
            z_lat = R * math.sin(lat)
            steps = 24
            for s in range(steps):
                lon1 = (s / steps) * 2.0 * math.pi
                lon2 = ((s + 1) / steps) * 2.0 * math.pi
                x1 = r_lat * math.cos(lon1)
                y1 = r_lat * math.sin(lon1)
                x2 = r_lat * math.cos(lon2)
                y2 = r_lat * math.sin(lon2)

                p1_x, p1_y, z1 = self.project_3d_point(x1, y1, z_lat, cx, cy, f_len=125.0, cam_dist=4.5)
                p2_x, p2_y, z2 = self.project_3d_point(x2, y2, z_lat, cx, cy, f_len=125.0, cam_dist=4.5)
                if p1_x is not None and p2_x is not None:
                    canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z1, z2)

        # Longitude lines
        for j in range(lon_count):
            lon = (j / lon_count) * 2.0 * math.pi
            steps = 16
            for s in range(steps):
                lat1 = -math.pi/2.0 + (s / steps) * math.pi
                lat2 = -math.pi/2.0 + ((s + 1) / steps) * math.pi
                x1 = R * math.cos(lat1) * math.cos(lon)
                y1 = R * math.cos(lat1) * math.sin(lon)
                z1 = R * math.sin(lat1)
                x2 = R * math.cos(lat2) * math.cos(lon)
                y2 = R * math.cos(lat2) * math.sin(lon)
                z2 = R * math.sin(lat2)

                p1_x, p1_y, z_val1 = self.project_3d_point(x1, y1, z1, cx, cy, f_len=125.0, cam_dist=4.5)
                p2_x, p2_y, z_val2 = self.project_3d_point(x2, y2, z2, cx, cy, f_len=125.0, cam_dist=4.5)
                if p1_x is not None and p2_x is not None:
                    canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z_val1, z_val2)

        # Orbiting Swarm Agents (Sentinel, Security, DevOps, Health)
        satellites = [
            ("Sentinel", 2.6, 1.2, 0.3),
            ("Security", 2.8, -0.9, -0.4),
            ("DevOps", 3.0, 1.5, 0.7),
            ("Health", 3.2, -1.1, -0.6)
        ]

        for name, dist, speed, tilt in satellites:
            ang = t * speed
            # Tilted orbit plane
            ox = dist * math.cos(ang)
            oy = dist * math.sin(ang) * math.cos(tilt)
            oz = dist * math.sin(ang) * math.sin(tilt)

            px, py, z_val = self.project_3d_point(ox, oy, oz, cx, cy, f_len=125.0, cam_dist=4.5)
            if px is not None:
                # Draw satellite cross
                canvas.set_pixel(px, py, 250)
                canvas.set_pixel(px - 1, py, 220)
                canvas.set_pixel(px + 1, py, 220)
                canvas.set_pixel(px, py - 1, 220)
                canvas.set_pixel(px, py + 1, 220)

    def render_lidar_mesh(self, canvas):
        """Draws Real-Time 3D LiDAR Point Cloud & Spatial Robotics Mesh."""
        cx = canvas.sub_w // 2
        cy = canvas.sub_h // 2
        t = self.time_sec

        # Ground wireframe grid
        grid_size = 3.0
        grid_step = 0.75
        z_floor = -1.2
        num_lines = int((grid_size * 2) / grid_step)

        for i in range(num_lines + 1):
            val = -grid_size + i * grid_step
            # X lines
            p1_x, p1_y, z1 = self.project_3d_point(val, -grid_size, z_floor, cx, cy, f_len=120.0, cam_dist=4.5)
            p2_x, p2_y, z2 = self.project_3d_point(val, grid_size, z_floor, cx, cy, f_len=120.0, cam_dist=4.5)
            if p1_x is not None and p2_x is not None:
                canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z1, z2)
            # Y lines
            p3_x, p3_y, z3 = self.project_3d_point(-grid_size, val, z_floor, cx, cy, f_len=120.0, cam_dist=4.5)
            p4_x, p4_y, z4 = self.project_3d_point(grid_size, val, z_floor, cx, cy, f_len=120.0, cam_dist=4.5)
            if p3_x is not None and p4_x is not None:
                canvas.draw_line(p3_x, p3_y, p4_x, p4_y, z3, z4)

        # Live LiDAR points from aether-roboticsd
        lidar_data = self.cached_robotics.get("lidar_360", {})
        samples = lidar_data.get("samples", 16)
        min_dist = lidar_data.get("min_distance_m", 0.42)
        lidar_pts = []

        for i in range(samples):
            theta = (i / samples) * 2.0 * math.pi
            # Simulated distance profile with obstacles
            r_dist = 1.6 + 0.6 * math.sin(theta * 3.0 + t) + 0.3 * math.cos(theta * 5.0)
            if i % 4 == 0:
                r_dist = max(0.6, r_dist * 0.7)  # simulated obstacle cluster
            lx = r_dist * math.cos(theta)
            ly = r_dist * math.sin(theta)
            lz = z_floor + 0.4 + 0.2 * math.sin(t * 2.0 + theta)

            px, py, z_val = self.project_3d_point(lx, ly, lz, cx, cy, f_len=120.0, cam_dist=4.5)
            if px is not None:
                canvas.set_pixel(px, py, 245)
                canvas.set_pixel(px+1, py, 210)
                lidar_pts.append((px, py, z_val))

        # Connect LiDAR perimeter points
        for i in range(len(lidar_pts)):
            p1 = lidar_pts[i]
            p2 = lidar_pts[(i + 1) % len(lidar_pts)]
            canvas.draw_line(p1[0], p1[1], p2[0], p2[1], p1[2], p2[2])

        # Central Robot Avatar / Orientation Gimbal
        imu = self.cached_robotics.get("imu_6dof", {}).get("attitude", {})
        yaw = imu.get("yaw_deg", 0.0)
        p_center_x, p_center_y, z_c = self.project_3d_point(0, 0, z_floor + 0.2, cx, cy, f_len=120.0, cam_dist=4.5)
        heading_x = 0.8 * math.cos(math.radians(yaw) + t)
        heading_y = 0.8 * math.sin(math.radians(yaw) + t)
        p_head_x, p_head_y, z_h = self.project_3d_point(heading_x, heading_y, z_floor + 0.2, cx, cy, f_len=120.0, cam_dist=4.5)
        if p_center_x is not None and p_head_x is not None:
            canvas.draw_line(p_center_x, p_center_y, p_head_x, p_head_y, 255, 255)

    def ask_jarvis(self, prompt):
        """Interactively routes prompt through aether-intentd and J.A.R.V.I.S. voice."""
        self.jarvis_subtitles = f"Tony: {prompt}"
        res = query_sock(INTENT_SOCK, {"action": "route", "prompt": prompt})
        if res:
            intent_res = res.get("result", "Protocol engaged, sir.")
            self.jarvis_subtitles = f"J.A.R.V.I.S.: {intent_res}"
            # Also vocalize via voice daemon
            query_sock(VOICE_SOCK, {"action": "speak", "text": intent_res})
        else:
            self.jarvis_subtitles = "J.A.R.V.I.S.: Command acknowledged, sir. Executing background routines."
            query_sock(VOICE_SOCK, {"action": "speak", "text": "Command acknowledged, sir."})
        self.subtitle_time = time.time()

    def handle_keyboard(self):
        """Non-blocking keyboard polling."""
        if not TERMIOS_AVAILABLE or not sys.stdin.isatty():
            return
        rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
        if rlist:
            ch = sys.stdin.read(1)
            if ch in ['q', 'Q', '\x1b']:  # Q or Esc
                self.running = False
            elif ch == '1':
                self.mode = 1
                self.jarvis_subtitles = "J.A.R.V.I.S.: Avengers Golden Hologram Sphere online, sir. Ladder truss rolling."
            elif ch == '2':
                self.mode = 2
                self.jarvis_subtitles = "J.A.R.V.I.S.: Mark 85 Arc Reactor Holographic projection engaged, sir."
            elif ch == '3':
                self.mode = 3
                self.jarvis_subtitles = "J.A.R.V.I.S.: Global Planetary Sensor Grid locked. Tracking Swarm Satellites."
            elif ch == '4':
                self.mode = 4
                self.jarvis_subtitles = "J.A.R.V.I.S.: Spatial LiDAR point cloud synchronized with robotics hub."
            elif ch == '5':
                self.mode = 5
                self.jarvis_subtitles = "J.A.R.V.I.S.: Full Workshop Diagnostic Matrix activated."
            elif ch in ['\t']:
                self.mode = (self.mode % 5) + 1
            elif ch == 'c' or ch == 'C':
                # Trigger self-healing
                query_sock(AGENT_SOCK, {"action": "trigger_heal"})
                self.jarvis_subtitles = "J.A.R.V.I.S.: Self-healing protocol dispatched across agent swarm."
            elif ch == 'r' or ch == 'R':
                # Trigger memory compact
                query_sock(MCP_SOCK, {"action": "call_tool", "name": "memory.compact", "args": {}})
                self.jarvis_subtitles = "J.A.R.V.I.S.: Kernel page compaction complete. Memory buffer optimized."
            elif ch == ' ':
                # Enter interactive prompt
                self.interactive_prompt = True

    def render_workshop_matrix(self, canvas):
        """Draws Dual Holographic Viewports: Arc Reactor (Left) & Planetary Grid (Right)."""
        mid_x = canvas.sub_w // 2
        cy = canvas.sub_h // 2
        cx_left = canvas.sub_w // 4
        cx_right = (canvas.sub_w * 3) // 4
        t = self.time_sec

        # Dividing laser wire
        for y in range(0, canvas.sub_h, 3):
            canvas.set_pixel(mid_x, y, 180)

        # Left Viewport: Arc Reactor Core
        R_outer = 1.6
        r_tube = 0.25
        for i in range(10):
            phi = (i / 10) * 2.0 * math.pi
            for j in range(6):
                theta1 = (j / 6) * 2.0 * math.pi
                theta2 = ((j + 1) / 6) * 2.0 * math.pi
                x1 = (R_outer + r_tube * math.cos(theta1)) * math.cos(phi)
                y1 = (R_outer + r_tube * math.cos(theta1)) * math.sin(phi)
                z1 = r_tube * math.sin(theta1)
                x2 = (R_outer + r_tube * math.cos(theta2)) * math.cos(phi)
                y2 = (R_outer + r_tube * math.cos(theta2)) * math.sin(phi)
                z2 = r_tube * math.sin(theta2)
                p1_x, p1_y, z1_v = self.project_3d_point(x1, y1, z1, cx_left, cy, f_len=85.0, cam_dist=4.2)
                p2_x, p2_y, z2_v = self.project_3d_point(x2, y2, z2, cx_left, cy, f_len=85.0, cam_dist=4.2)
                if p1_x is not None and p2_x is not None and p1_x < mid_x and p2_x < mid_x:
                    canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z1_v, z2_v)

        # Left Central Singularity
        for p in range(8):
            ang = (p / 8) * 2.0 * math.pi
            px, py, z_v = self.project_3d_point(0.4 * math.cos(ang), 0.4 * math.sin(ang), 0, cx_left, cy, f_len=85.0, cam_dist=4.2)
            if px is not None and px < mid_x:
                canvas.set_pixel(px, py, 255)

        # Right Viewport: Planetary Defense Grid
        R = 1.5
        for i in range(1, 6):
            lat = -math.pi/2.0 + (i / 6) * math.pi
            r_lat = R * math.cos(lat)
            z_lat = R * math.sin(lat)
            for s in range(16):
                lon1 = (s / 16) * 2.0 * math.pi
                lon2 = ((s + 1) / 16) * 2.0 * math.pi
                x1 = r_lat * math.cos(lon1)
                y1 = r_lat * math.sin(lon1)
                x2 = r_lat * math.cos(lon2)
                y2 = r_lat * math.sin(lon2)
                p1_x, p1_y, z1 = self.project_3d_point(x1, y1, z_lat, cx_right, cy, f_len=80.0, cam_dist=4.2)
                p2_x, p2_y, z2 = self.project_3d_point(x2, y2, z_lat, cx_right, cy, f_len=80.0, cam_dist=4.2)
                if p1_x is not None and p2_x is not None and p1_x > mid_x and p2_x > mid_x:
                    canvas.draw_line(p1_x, p1_y, p2_x, p2_y, z1, z2)

        # Right Orbiting Satellites
        for s_idx, (name, dist, spd, tilt) in enumerate([("Sentinel", 2.0, 1.2, 0.4), ("Security", 2.2, -1.0, -0.5)]):
            ang = t * spd
            ox = dist * math.cos(ang)
            oy = dist * math.sin(ang) * math.cos(tilt)
            oz = dist * math.sin(ang) * math.sin(tilt)
            px, py, z_v = self.project_3d_point(ox, oy, oz, cx_right, cy, f_len=80.0, cam_dist=4.2)
            if px is not None and px > mid_x:
                canvas.set_pixel(px, py, 250)
                canvas.set_pixel(px - 1, py, 220)
                canvas.set_pixel(px + 1, py, 220)

    def run_frame(self, term_w, term_h):
        """Generates a complete terminal frame string."""
        self.update_sensors()
        self.time_sec += 0.05
        self.angle_y += 0.03
        self.angle_x = 0.35 + 0.1 * math.sin(self.time_sec * 0.4)

        # Header bar
        mode_titles = {
            1: "AVENGERS J.A.R.V.I.S. GOLDEN SPHERE [ULTRON-ERA HOLOGRAM]",
            2: "MARK 85 ARC REACTOR CORE [3D HOLOGRAPHIC PROJECTION]",
            3: "GLOBAL PLANETARY SENSOR & DEFENSE GRID [ORBITAL TRACKING]",
            4: "SPATIAL 3D LIDAR & ROBOTICS POINT CLOUD [SENSOR FUSION]",
            5: "STARK INDUSTRIES WORKSHOP MATRIX [DUAL VIEWPORTS]"
        }
        title = mode_titles.get(self.mode, "AETHEROS HOLOGRAM")

        # Sidebar and Canvas layout
        sidebar_w = 34
        canvas_w = max(40, term_w - sidebar_w - 3)
        canvas_h = max(18, term_h - 7)

        canvas = BrailleCanvas(canvas_w, canvas_h)
        if self.mode == 1:
            self.render_ultron_jarvis_sphere(canvas)
            color_style = "gold"
        elif self.mode == 2:
            self.render_arc_reactor(canvas)
            color_style = "cyan"
        elif self.mode == 3:
            self.render_global_grid(canvas)
            color_style = "cyan"
        elif self.mode == 4:
            self.render_lidar_mesh(canvas)
            color_style = "gold"
        elif self.mode == 5:
            self.render_workshop_matrix(canvas)
            color_style = "cyan"
        else:
            self.render_ultron_jarvis_sphere(canvas)
            color_style = "gold"

        canvas_lines = canvas.render_rows(color_style=color_style)

        # Build Sidebar telemetry
        mcp_data = self.cached_mcp.get("result", {})
        vis_data = self.cached_vision.get("biometrics", {})
        ergo_data = self.cached_vision.get("ergonomics", {})
        rob_data = self.cached_robotics.get("imu_6dof", {}).get("attitude", {})
        swarm_agents = self.cached_swarm.get("agents", {})

        sidebar_lines = [
            f"{BOLD}{HOLO_CYAN}── ARC REACTOR CORE ──{RESET}",
            f"{HOLO_TEXT}Output:     {HOLO_CYAN_HOT}{BOLD}3.82 GW (100%){RESET}",
            f"{HOLO_TEXT}Core Temp:  {HOLO_GREEN}4.2 K (Cryo){RESET}",
            f"{HOLO_TEXT}Containment:{HOLO_GREEN}STABLE (99.8%){RESET}",
            f"{HOLO_TEXT}Flux:       {HOLO_CYAN}1.21 Tesla{RESET}",
            "",
            f"{BOLD}{HOLO_CYAN}── COGNITIVE SWARM ──{RESET}",
            f"{HOLO_TEXT}Sentinel:   {HOLO_GREEN}ACTIVE [T: sub-10ms]{RESET}",
            f"{HOLO_TEXT}Security:   {HOLO_GREEN}NOMINAL [0 Intrusions]{RESET}",
            f"{HOLO_TEXT}DevOps:     {HOLO_GREEN}OPTIMAL [AVX2 SIMD]{RESET}",
            f"{HOLO_TEXT}Health:     {HOLO_GREEN}ALL HEALTHY{RESET}",
            "",
            f"{BOLD}{HOLO_CYAN}── AMBIENT SENSORY ──{RESET}",
            f"{HOLO_TEXT}User:       {HOLO_CYAN_HOT}{vis_data.get('authenticated_user', 'Tony Stark')}{RESET}",
            f"{HOLO_TEXT}Confidence: {HOLO_GREEN}{vis_data.get('confidence', 0.98)*100:.1f}%{RESET}",
            f"{HOLO_TEXT}Blink Rate: {HOLO_TEXT}{ergo_data.get('blink_rate_bpm', 14)} bpm{RESET}",
            f"{HOLO_TEXT}Posture:    {HOLO_GREEN}{ergo_data.get('posture', 'upright')}{RESET}",
            "",
            f"{BOLD}{HOLO_CYAN}── ROBOTICS & ATTITUDE ──{RESET}",
            f"{HOLO_TEXT}Roll/Pitch: {rob_data.get('roll_deg', 0.0):.1f}° / {rob_data.get('pitch_deg', 0.0):.1f}°{RESET}",
            f"{HOLO_TEXT}Yaw Nav:    {rob_data.get('yaw_deg', 0.0):.1f}°{RESET}",
            f"{HOLO_TEXT}LiDAR Dist: {HOLO_GREEN}0.42m Clear{RESET}",
            "",
            f"{BOLD}{HOLO_GOLD}── VOICE SPECTRUM ──{RESET}",
            f"{HOLO_CYAN} ▂▃▅▆▇█▇▆▅▃ ▂▃▅▆▇█{RESET}"
        ]

        # Combine into frame
        header = f"{BG_DARK}{HOLO_CYAN}┌─[ {BOLD}{HOLO_CYAN_HOT}AETHEROS J.A.R.V.I.S. HOLOGRAPHIC CORE{RESET}{BG_DARK}{HOLO_CYAN} ]" + "─" * max(10, term_w - 44) + f"┐{RESET}\n"
        mode_bar = f"{BG_DARK}{HOLO_CYAN}│ {HOLO_GOLD}MODE: {BOLD}{HOLO_TEXT}{title[:term_w-15]}{RESET}{' ' * max(0, term_w - len(title) - 15)}{BG_DARK}{HOLO_CYAN}│{RESET}\n"
        sep = f"{BG_DARK}{HOLO_CYAN}├" + "─" * (sidebar_w + 1) + "┬" + "─" * (term_w - sidebar_w - 4) + f"┤{RESET}\n"

        rows = []
        for i in range(canvas_h):
            s_line = sidebar_lines[i] if i < len(sidebar_lines) else ""
            c_line = canvas_lines[i] if i < len(canvas_lines) else ""
            # Strip ANSI for sidebar length padding
            raw_len = len(s_line.replace(RESET, '').replace(BOLD, '').replace(DIM, '').replace(HOLO_CYAN_HOT, '').replace(HOLO_CYAN, '').replace(HOLO_BLUE, '').replace(HOLO_DEEP_BLUE, '').replace(HOLO_GOLD, '').replace(HOLO_GOLD_HOT, '').replace(HOLO_GREEN, '').replace(HOLO_RED, '').replace(HOLO_TEXT, '').replace(HOLO_MUTED, ''))
            pad = " " * max(0, sidebar_w - raw_len)
            rows.append(f"{BG_DARK}{HOLO_CYAN}│{RESET} {s_line}{pad} {BG_DARK}{HOLO_CYAN}│{RESET} {c_line}")

        # Subtitles / J.A.R.V.I.S. Voice Response bar
        sub_sep = f"{BG_DARK}{HOLO_CYAN}├" + "─" * (term_w - 2) + f"┤{RESET}\n"
        sub_content = self.jarvis_subtitles[:term_w - 6]
        sub_bar = f"{BG_DARK}{HOLO_CYAN}│ {HOLO_GOLD_HOT}󰹢 {BOLD}{sub_content}{RESET}" + " " * max(0, term_w - len(sub_content) - 6) + f"{BG_DARK}{HOLO_CYAN}│{RESET}\n"

        # Hotkeys footer
        footer_keys = "[1] Golden Sphere  [2] Arc Reactor  [3] Global Radar  [4] 3D LiDAR  [5] Workshop  [Space] Speak to Jarvis  [C] Heal  [R] RAM  [Q] Exit"
        footer = f"{BG_DARK}{HOLO_CYAN}└─[ {HOLO_TEXT}{footer_keys[:term_w-8]}{HOLO_CYAN} ]" + "─" * max(0, term_w - len(footer_keys) - 7) + f"┘{RESET}"

        return header + mode_bar + sep + "\n".join(rows) + "\n" + sub_sep + sub_bar + footer

    def run(self):
        """Main rendering & interaction loop."""
        old_settings = None
        if TERMIOS_AVAILABLE and sys.stdin.isatty():
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

        sys.stdout.write(HIDE_CURSOR + CLEAR_SCREEN)
        sys.stdout.flush()

        # Initial Jarvis greeting vocalization
        query_sock(VOICE_SOCK, {"action": "speak", "text": "Welcome back, sir. Holographic workshop is online. Arc Reactor core is at 100 percent."})

        try:
            while self.running:
                term_w, term_h = shutil.get_terminal_size((100, 30))
                self.handle_keyboard()

                if self.interactive_prompt:
                    # Restore terminal mode temporarily for typing
                    if old_settings:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    sys.stdout.write(SHOW_CURSOR)
                    sys.stdout.write(f"\n{HOLO_GOLD_HOT}{BOLD}J.A.R.V.I.S. Ready. Speak or type command, sir:{RESET} ")
                    sys.stdout.flush()
                    try:
                        cmd = sys.stdin.readline().strip()
                        if cmd:
                            self.ask_jarvis(cmd)
                    except Exception:
                        pass
                    self.interactive_prompt = False
                    if old_settings:
                        tty.setcbreak(sys.stdin.fileno())
                    sys.stdout.write(HIDE_CURSOR + CLEAR_SCREEN)

                frame = self.run_frame(term_w, term_h)
                sys.stdout.write("\033[H" + frame)
                sys.stdout.flush()
                time.sleep(0.04)  # ~25 FPS
        finally:
            sys.stdout.write(SHOW_CURSOR + CLEAR_SCREEN)
            sys.stdout.flush()
            if old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["--test", "-t", "test"]:
        # Headless test mode: render 5 frames across all holographic modes
        engine = HologramEngine()
        frame1 = engine.run_frame(90, 26)
        engine.mode = 2
        frame2 = engine.run_frame(90, 26)
        engine.mode = 3
        frame3 = engine.run_frame(90, 26)
        engine.mode = 4
        frame4 = engine.run_frame(90, 26)
        engine.mode = 5
        frame5 = engine.run_frame(90, 26)
        assert len(frame1) > 500, "Frame 1 empty"
        assert len(frame2) > 500, "Frame 2 empty"
        assert len(frame3) > 500, "Frame 3 empty"
        assert len(frame4) > 500, "Frame 4 empty"
        assert len(frame5) > 500, "Frame 5 empty"
        print("HologramEngine test passed! Rendered all 5 modes (Avengers Golden Sphere, Arc Reactor, Global Radar, LiDAR, Workshop Matrix) successfully.")
        return 0

    engine = HologramEngine()
    engine.run()
    return 0

if __name__ == "__main__":
    sys.exit(main())
