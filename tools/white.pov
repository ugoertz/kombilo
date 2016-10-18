// Usage
// povray white.pov +H300 +W300 Declare=Seed=10 -Ow.png +UA
// (replace 10 by some other number to get "randomly" different stone)
// Then use GIMP to add drop shadow
// (or see http://www.imagico.de/pov/icons.php - but I did not try this yet)

#include "colors.inc"

camera {
    location <0,15,0>
    right x
    angle 9
    look_at   <.0, .0,  .0>
}

light_source { <-500, 1500, 500> color White*0.5 }
light_source { <+50, 150, 50> color White*0.1 }
light_source { <150, 150, 50> color White*0.1 }
light_source { <+50, 50, 150> color White*0.2 }

// seed for random number generator
#ifndef (Seed)
      #declare Seed = 0;
#end

#local r = seed(Seed);

sphere { 0 1.152
    texture{
        pigment {
            marble // gradient x
            color_map {
                [0.0 color White*1.3]
                [0.2 color White*1.3]
                [0.45 color Gray95*1.2]
                [0.55 color Gray95*1.2]
                [0.75 color White*1.3]
                [1.0 color White*1.3]
            }
            frequency 1.5 + 2.5 * rand(r)
            turbulence 0.2
        }
        finish { specular .8 roughness .001 }
        translate rand(r)*15
        rotate y*rand(r)*360
    }
    scale < 1,0.4,1>
    translate <-0.023, 0, 0.023>
}

