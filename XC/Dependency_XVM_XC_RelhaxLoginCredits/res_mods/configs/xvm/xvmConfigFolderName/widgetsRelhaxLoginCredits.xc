{
    // Relhax Logo Palette:
    // #84c4ca      #4a6f71     #272526     #00e300             #75be81 
    // (LT Blue)    (DK Blue)   (DK grey)   (OM eyes green)     (OM leaves green)
    
    /*
            RELHAX MODPACK TEAM
    Developed by:       -- Translated by:
    Willster419         en Rkk1945
    elektrosmoker       en Merkk
    Dirty20067          de Grumpelumpf
    123Gauss            pl Nullmaruzero
    The_Illusion        pl Neoros
                        fr Toshiro
    Media Relations:        es LordFelix
    Silvers_            ru DrWeb7_1
    */
    
    "LF_OM_Logo": {
        "enabled":              true,
        "layer":                "top",
        "type":                 "extrafield",
        "formats": [
            {
                "x":           -180,            // Horizontal position.
                "y":            285,            // Vertical position.
                "width":        100,            // Width.
                "height":       100,            // Height.
                "screenHAlign": "center",       // Horizontal alignment of field at screen ("left", "center", "right").
                "screenVAlign": "center",
                "bgColor":      "0x84c4ca",
                "format":       "<img src='xvm://res/icons/Relhax/Odem_Mortis_Logo_96.png' width='96' height='96'>"
            }
        ]
    },
    "LF_Relhax_Logo": {
        "enabled":              true,
        "layer":                "top",
        "type":                 "extrafield",
        "formats": [
            {
                "x":            180,            // Horizontal position.
                "y":            285,            // Vertical position.
                "width":        100,            // Width.
                "height":       100,            // Height.
                "screenHAlign": "center",       // Horizontal alignment of field at screen ("left", "center", "right").
                "screenVAlign": "center",
                "bgColor":      "0x84c4ca",
                "format":       "<img src='xvm://res/icons/Relhax/Relhax_Logo_96.png'>"
            }
        ]
    },
    "LF_Relhax_Modpack": {
        "enabled":              true,
        "layer":                "top",
        "type":                 "extrafield",
        "formats": [
            {
                "x":            0,              // Horizontal position.
                "y":            385,            // Vertical position. -23px (up) if another line is needed.
                "width":        450,            // Width.
                "height":       80,             // Height.
                "screenHAlign": "center",       // Horizontal alignment of field at screen ("left", "center", "right").
                "screenVAlign": "center",       // Vertical alignment of field at screen ("top", "center", "botton").
                "shadow":       { "enabled": true, "distance": 0, "angle": 0, "color": "0x000000", "alpha": 100, "blur": 2, "strength": 6 },
                "textFormat":   { "font": "DinPro-Bold", "color": "0x84c4ca", "size": 55, "align": "center", "valign": "top"},
                "format":       "Relhax Modpack"
            }
        ]
    },
    "LF_Credits_Devs": {
        "enabled":              true,
        "layer":                "top",
        "type":                 "extrafield",
        "formats": [
            {
                "x":           -370,            // Horizontal position.
                "y":            268,            // Vertical position.  -23px (up) if another line is needed.
                "width":        200,            // Width.
                "height":       300,            // Height.
                "screenHAlign": "center",       // Horizontal alignment of field at screen ("left", "center", "right").
                "screenVAlign": "center",       // Vertical alignment of field at screen ("top", "center", "botton").
                "shadow":       { "enabled": true, "distance": 0, "angle": 0, "color": "0x000000", "alpha": 100, "blur": 2, "strength": 6 },
                "textFormat":   { "font": "DinPro-Bold", "color": "0x75bc81", "size": 20, "align": "right", "valign": "top"},
                "format":       "<u><font color='#84c4ca'>Developed by:</font></u> \nWillster419 <img src='xvm://res/icons/flags/us.png' width='16' height='13' vspace='-1'> \nelektrosmoker <img src='xvm://res/icons/flags/at.png' width='16' height='13' vspace='-1'> \ndirty20067 <img src='xvm://res/icons/flags/de.png' width='16' height='13' vspace='-1'> \n123Gauss <img src='xvm://res/icons/flags/de.png' width='16' height='13' vspace='-1'> \nThe_Illusion <img src='xvm://res/icons/flags/ca.png' width='16' height='13' vspace='-1'> \nSaucE <img src='xvm://res/icons/flags/us.png' width='16' height='13' vspace='-1'> \nZethen <img src='xvm://res/icons/flags/us.png' width='16' height='13' vspace='-1'>\n\n<u><font color='#84c4ca'>Media Relations:</font></u> \nSilvers_ <img src='xvm://res/icons/flags/us.png' width='16' height='13' vspace='-1'>"
            }
        ]
    },
    "LF_Credits_Translators": {
        "enabled":              true,
        "layer":                "top",
        "type":                 "extrafield",
        "formats": [
            {
                "x":            370,            // Horizontal position.
                "y":            291,            // Vertical position.
                "width":        200,            // Width.
                "height":       250,            // Height.
                "screenHAlign": "center",       // Horizontal alignment of field at screen ("left", "center", "right").
                "screenVAlign": "center",       // Vertical alignment of field at screen ("top", "center", "botton").
                "shadow":       { "enabled": true, "distance": 0, "angle": 0, "color": "0x000000", "alpha": 100, "blur": 2, "strength": 6 },
                "textFormat":   { "font": "DinPro-Bold", "color": "0x75bc81", "size": 20, "align": "left", "valign": "top"},
                "format":       "<img src='xvm://res/icons/flags/unknown.png' width='16' height='13' vspace='-1'> <u><font color='#84c4ca'>Translated by:</font></u>\n<img src='xvm://res/icons/flags/gb.png' width='16' height='13' vspace='-1'> Rkk1945\n<img src='xvm://res/icons/flags/gb.png' width='16' height='13' vspace='-1'> Merkk\n<img src='xvm://res/icons/flags/de.png' width='16' height='13' vspace='-1'> Grumpelumpf\n<img src='xvm://res/icons/flags/pl.png' width='16' height='13' vspace='-1'> Nullmaruzero\n<img src='xvm://res/icons/flags/pl.png' width='16' height='13' vspace='-1'> Neoros\n<img src='xvm://res/icons/flags/fr.png' width='16' height='13' vspace='-1'> Toshiro\n<img src='xvm://res/icons/flags/es.png' width='16' height='13' vspace='-1'> LordFelix\n<img src='xvm://res/icons/flags/ru.png' width='16' height='13' vspace='-1'> DrWeb7_1"
            }
        ]
    }
      
}
