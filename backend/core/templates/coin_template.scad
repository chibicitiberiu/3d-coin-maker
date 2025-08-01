// Coin Generator Template
// Variables will be substituted by Python generator

$VARIABLES$

// Use reasonable global resolution
$fn = 32;

module coin_shape_2d() {
    if (shape == "circle") {
        circle(d=diameter, $fn=64);  // Reasonable resolution for smooth edges
    } else if (shape == "square") {
        square([diameter, diameter], center=true);
    } else if (shape == "hexagon") {
        circle(d=diameter, $fn=6);
    } else if (shape == "octagon") {
        circle(d=diameter, $fn=8);
    } else {
        circle(d=diameter, $fn=64);  // Reasonable resolution for default case too
    }
}

module base_coin() {
    // Generate base coin from 0 to thickness-relief_depth
    linear_extrude(height=thickness - relief_depth) {
        coin_shape_2d();
    }
}

module relief_surface() {
    // Generate relief surface with proper scaling
    // Surface generates heights 0-100, so divide by 100 for proper relief_depth scaling
    translate([offset_x_mm, offset_y_mm, 0])
    rotate([0, 0, rotation])
    scale([final_scale_x, final_scale_y, relief_depth/100])
    surface(file=heightmap_path, center=true, convexity=10);
}

module clipped_relief() {
    intersection() {
        // Clip relief to coin shape boundaries
        linear_extrude(height=relief_depth + 1) {
            coin_shape_2d();
        }
        relief_surface();
    }
}

// Create coin by combining base and relief layers
union() {
    base_coin();
    translate([0, 0, thickness - relief_depth])
    clipped_relief();
}