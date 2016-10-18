// Usage
// povray black.pov +H300 +W300 -Ob.png +UA
// Then use GIMP to add drop shadow
// (or see http://www.imagico.de/pov/icons.php - but I did not try this yet)

// See also https://github.com/zpmorgan/gostones-render
// and http://senseis.xmp.net/?POVRay

#include "colors.inc"

camera {
    location <0,15,0>
    right x
    angle 9
    look_at   <.0, .0,  .0>
}

light_source { <-500, 1500, 500> color White*0.2 }
light_source { <+50, 150, 50> color White*0.03 }
light_source { <150, 150, 50> color White*0.03 }
light_source { <+50, 50, 150> color White*0.03 }


sphere { 0 1.152
    texture {
        pigment { Black }
        finish { specular .6 roughness .025 }
    }
    scale < 1,0.4,1>
    translate <-0.023, 0, 0.023>
}

