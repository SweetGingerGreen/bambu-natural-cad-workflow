// =============================================================
// F2 v5 · 镂空绑绳版空气凤梨球
// Lattice-only spherical Tillandsia hanger, no plant collars, no joinery holes
//
// 用户要求:
//   - 去掉圆形植物座,空气凤梨直接塞进镂空结构
//   - 整体稍微缩小
//   - 上下半球连接不做孔位,后续用绳子捆绑
//
// 导出:
//   openscad -o f2_top_v5_lattice_tie.stl    -D 'render_part="top"'    F2-sphere-v5-lattice-tie.scad
//   openscad -o f2_bottom_v5_lattice_tie.stl -D 'render_part="bottom"' F2-sphere-v5-lattice-tie.scad
//
// 注意:
//   - both_preview 只用于检查装配关系,不要导出给 Bambu Studio 打印
//   - 镂空藤条是视觉/托举结构,不是承重安全件
// =============================================================

/* [Render] */
render_part = "top"; // [top, bottom, both_preview]

/* [Sphere] */
sphere_d   = 210;
vine_count = 7;
vine_turns = 1.05;
vine_w     = 5.8;
vine_steps = 24;

/* [Equator tie seam] */
eq_ring_w = 8;
eq_ring_h = 6;

/* [Hanging loop] */
hang_ring_outer = 22;
hang_ring_inner = 10;
hang_ring_t     = 5.5;

/* [Quality] */
$fa = 10;
$fs = 1.8;

// =============================================================
// Main
// =============================================================
if (render_part == "top") {
    top_half_print();
} else if (render_part == "bottom") {
    bottom_half_print();
} else if (render_part == "both_preview") {
    top_half_assembly();
    bottom_half_assembly();
}

// =============================================================
// Printable parts
// =============================================================
module top_half_print() {
    top_half_assembly();
}

module bottom_half_print() {
    // Export mirrored so the equator seam is the flat print face.
    mirror([0,0,1]) bottom_half_assembly();
}

module top_half_assembly() {
    union() {
        lattice_shell(top=true);
        equator_ring(z0=0, h=eq_ring_h);
        top_hanger();
    }
}

module bottom_half_assembly() {
    union() {
        lattice_shell(top=false);
        equator_ring(z0=-eq_ring_h, h=eq_ring_h);
        translate([0,0,-sphere_d/2 + 4])
            sphere(d=14, $fn=14);
    }
}

// =============================================================
// Lattice
// =============================================================
module lattice_shell(top=true) {
    union() {
        // Two opposite spiral families create diamond-like openings.
        for (hand=[-1, 1]) {
            for (i=[0:vine_count-1]) {
                rotate([0,0,i*360/vine_count + (hand < 0 ? 180/vine_count : 0)])
                    spiral_vine(top=top, hand=hand);
            }
        }
    }
}

module spiral_vine(top=true, hand=1) {
    R = sphere_d/2;
    t_start = top ? 0.01 : 0.025;
    t_end   = top ? 0.975 : 0.99;

    for (i=[0:vine_steps-1]) {
        t1 = t_start + i / vine_steps * (t_end - t_start);
        t2 = t_start + (i + 1) / vine_steps * (t_end - t_start);

        th1 = top ? t1 * 90 : 90 + t1 * 90;
        th2 = top ? t2 * 90 : 90 + t2 * 90;
        ph1 = hand * t1 * vine_turns * 360;
        ph2 = hand * t2 * vine_turns * 360;

        p1 = sph_pt(R, th1, ph1);
        p2 = sph_pt(R, th2, ph2);

        hull() {
            translate(p1) sphere(d=vine_w, $fn=8);
            translate(p2) sphere(d=vine_w, $fn=8);
        }
    }
}

function sph_pt(R, theta_deg, phi_deg) = [
    R * sin(theta_deg) * cos(phi_deg),
    R * sin(theta_deg) * sin(phi_deg),
    R * cos(theta_deg)
];

// =============================================================
// Equator seam
// =============================================================
module equator_ring(z0=0, h=eq_ring_h) {
    Ro = sphere_d/2;
    Ri = sphere_d/2 - eq_ring_w;
    translate([0,0,z0])
        difference() {
            cylinder(r=Ro, h=h);
            translate([0,0,-1])
                cylinder(r=Ri, h=h + 2);
        }
}

// =============================================================
// Hanging loop
// =============================================================
module top_hanger() {
    translate([0,0,sphere_d/2 - 4])
        sphere(d=22, $fn=16);

    translate([0,0,sphere_d/2 + 8])
        rotate([90,0,0])
            difference() {
                cylinder(d=hang_ring_outer, h=hang_ring_t, center=true);
                cylinder(d=hang_ring_inner, h=hang_ring_t + 1, center=true);
            }

    // Short twin braces tie the loop back into the top cap.
    hull() {
        translate([-7,0,sphere_d/2 - 1]) sphere(d=8, $fn=12);
        translate([-7,0,sphere_d/2 + 8]) sphere(d=8, $fn=12);
    }
    hull() {
        translate([7,0,sphere_d/2 - 1]) sphere(d=8, $fn=12);
        translate([7,0,sphere_d/2 + 8]) sphere(d=8, $fn=12);
    }
}

