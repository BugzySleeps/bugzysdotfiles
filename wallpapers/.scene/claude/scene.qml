import QtQuick
import QtQuick.Shapes

// The claude wallpaper's moving scene, drawn by liquid's desktop/Wallpaper.qml over claude.png (a still of this).
// The Claude spark on the right, each ray stretching with its own slice of the music; a ring of bars round it,
// rings thrown off on the beat, a glow that swells, the 6-cookies drifting about, and the little Claude
// orbiting the logo like a moon, behind it on the far side of its ring.
//
// Its colours follow the album's when liquid's album colours are on (Settings.artAccent): `feed.accent` is then the
// shell's accent, and every colour here (the pictures through hue.frag) turns from Claude orange to match it.
//
// `feed` comes from the shell (15 frames a second idle, 25 with music): time (s), flow (time sped up by the music), energy and beat (0–1), bands (cava's
// bars, 0–1), playing. With no feed (or nothing playing) it idles: everything breathes, the moon keeps going.
Item {
    id: root

    property QtObject feed: null
    readonly property real t: feed ? feed.time : 0
    readonly property real flow: feed ? feed.flow : 0
    readonly property real energy: feed ? feed.energy : 0
    readonly property real beat: feed ? feed.beat : 0
    readonly property var bands: feed ? feed.bands : []
    readonly property bool playing: feed ? feed.playing : false
    function band(i) {
        return i < bands.length ? bands[i] : 0;
    }

    readonly property real cx: width * 0.73       // the logo (make.py's LOGO, so the backdrop warms behind it)
    readonly property real cy: height * 0.5
    readonly property real r: height * 0.2        // the spark's longest ray
    // ── colour: Claude orange, or turned to the album's ──────────────
    readonly property color home: "#ff8e68"       // the accent liquid takes from claude.png itself
    property color tone: feed && feed.accent ? feed.accent : home
    Behavior on tone {
        ColorAnimation {
            duration: 1200
            easing.type: Easing.InOutQuad
        }
    }
    // how far round the colour wheel, and how colourful (a grey cover: none)
    readonly property real shift: tone.hsvHue < 0 ? 0 : tone.hsvHue - home.hsvHue
    readonly property real sat: Math.min(1.2, Math.max(0, tone.hsvSaturation / home.hsvSaturation))
    function hued(c) {
        c = Qt.color(c);
        const h = c.hsvHue < 0 ? 0 : c.hsvHue;
        return Qt.hsva(((h + shift) % 1 + 1) % 1, Math.min(1, c.hsvSaturation * sat), c.hsvValue, c.a);
    }
    readonly property color orange: hued("#d97757")
    readonly property color hot: hued("#ff8a50")

    // a picture, turned the same way (hue.frag)
    component HuedImage: Item {
        property alias source: img.source
        property alias sourceSize: img.sourceSize
        property alias mipmap: img.mipmap
        property alias fillMode: img.fillMode
        property alias asynchronous: img.asynchronous
        Image {
            id: img
            anchors.fill: parent
            visible: false
        }
        ShaderEffect {
            anchors.fill: parent
            property var source: img
            property real shift: root.shift
            property real sat: root.sat
            fragmentShader: "hue.frag.qsb"
        }
    }

    HuedImage {
        anchors.fill: parent
        source: "bg.jpg"
        fillMode: Image.PreserveAspectCrop
        sourceSize.width: 1920
        sourceSize.height: 1080
        asynchronous: false
    }

    // ── the 6-cookies ───────────────────────────────────────────────
    Repeater {
        model: [
            { x: 0.08, y: 0.15, s: 0.17, line: false, spin: 1.2, ph: 0.0 },
            { x: 0.23, y: 0.73, s: 0.10, line: true, spin: -2.0, ph: 1.3 },
            { x: 0.37, y: 0.22, s: 0.07, line: true, spin: 2.5, ph: 2.1 },
            { x: 0.11, y: 0.50, s: 0.055, line: true, spin: -3.0, ph: 3.7 },
            { x: 0.45, y: 0.86, s: 0.14, line: false, spin: -0.8, ph: 0.6 },
            { x: 0.53, y: 0.11, s: 0.05, line: true, spin: 3.2, ph: 4.4 },
            { x: 0.56, y: 0.62, s: 0.045, line: false, spin: -2.6, ph: 5.0 },
            { x: 0.93, y: 0.12, s: 0.09, line: true, spin: 1.8, ph: 2.8 },
            { x: 0.96, y: 0.87, s: 0.16, line: false, spin: -1.0, ph: 1.9 },
            { x: 0.77, y: 0.91, s: 0.06, line: true, spin: 2.2, ph: 3.1 },
            { x: 0.31, y: 0.47, s: 0.035, line: false, spin: 4.0, ph: 0.9 },
            { x: 0.90, y: 0.56, s: 0.04, line: false, spin: -3.5, ph: 5.6 },
            { x: 0.65, y: 0.17, s: 0.035, line: true, spin: 3.8, ph: 4.0 },
            { x: 0.17, y: 0.92, s: 0.05, line: true, spin: -2.4, ph: 2.4 }
        ]
        HuedImage {
            required property var modelData
            readonly property real size: modelData.s * root.height
            source: modelData.line ? "cookie-line.png" : "cookie.png"
            width: size
            height: size
            sourceSize.width: 512
            sourceSize.height: 512
            smooth: true
            mipmap: true
            x: modelData.x * root.width - size / 2 + Math.sin(root.t * 0.21 + modelData.ph) * root.height * 0.012
            y: modelData.y * root.height - size / 2 + Math.cos(root.t * 0.17 + modelData.ph * 1.7) * root.height * 0.014
            rotation: modelData.ph * 40 + root.t * modelData.spin
            scale: 1 + root.energy * 0.07 + root.beat * (modelData.line ? 0.05 : 0.03)
            opacity: 0.8 + root.energy * 0.2
        }
    }

    // ── sparks drifting round the logo ──────────────────────────────
    Repeater {
        model: 14
        HuedImage {
            required property int index
            readonly property real a: index * 2.4 + root.t * (0.05 + (index % 5) * 0.018) * (index % 2 ? 1 : -1)
            readonly property real d: root.r * (1.55 + (index * 0.37) % 1.3)
            readonly property real size: root.height * (0.003 + (index % 4) * 0.0016) * (1 + root.energy * 0.8)
            source: "dot.png"
            width: size * 3
            height: size * 3
            x: root.cx + Math.cos(a) * d - width / 2
            y: root.cy + Math.sin(a) * d * 0.8 - height / 2
            opacity: (0.25 + 0.35 * (0.5 + 0.5 * Math.sin(root.t * (0.8 + index * 0.13) + index))) * (0.6 + root.energy)
        }
    }

    // ── glow ─────────────────────────────────────────────────────────
    HuedImage {
        source: "glow.png"
        readonly property real size: root.r * (4.6 + root.energy * 1.2 + root.beat * 0.6)
        width: size
        height: size
        x: root.cx - size / 2
        y: root.cy - size / 2
        opacity: 0.42 + root.energy * 0.35 + 0.05 * Math.sin(root.t * 0.9)
    }

    // ── rings thrown off on the beat ─────────────────────────────────
    property int ringNext: 0
    property real lastBeat: 0
    property real lastRing: -10
    onBeatChanged: {
        if (playing && beat > 0.5 && beat - lastBeat > 0.1 && t - lastRing > 0.28) {
            rings.itemAt(ringNext).go();
            ringNext = (ringNext + 1) % rings.count;
            lastRing = t;
        }
        lastBeat = beat;
    }
    Repeater {
        id: rings
        model: 5
        Rectangle {
            id: ring
            property real p: 1
            function go() {
                grow.restart();
            }
            readonly property real size: root.r * 2.3 * (1 + p * 1.4)
            width: size
            height: size
            radius: size / 2
            x: root.cx - size / 2
            y: root.cy - size / 2
            color: "transparent"
            border.width: 1 + (1 - p) * 2.5
            border.color: root.hot
            opacity: (1 - p) * 0.55
            visible: p < 1
            NumberAnimation {
                id: grow
                target: ring
                property: "p"
                from: 0
                to: 1
                duration: 1300
                easing.type: Easing.OutCubic
            }
        }
    }

    // ── the far half of the moon's orbit (behind the logo) ───────────
    readonly property real orx: r * 1.85
    readonly property real ory: r * 0.42
    readonly property real tilt: -16
    component OrbitHalf: Shape {
        id: half
        property real from: 0
        x: root.cx
        y: root.cy
        rotation: root.tilt
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: Qt.alpha(root.hued("#ff8f5c"), 0.28 + root.energy * 0.25)
            strokeWidth: 1.6
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathAngleArc {
                radiusX: root.orx
                radiusY: root.ory
                startAngle: half.from
                sweepAngle: 180
            }
        }
    }
    OrbitHalf {
        from: 180
        z: 1
    }

    // ── the spark ────────────────────────────────────────────────────
    Item {
        id: logo
        z: 5
        x: root.cx
        y: root.cy
        rotation: root.t * 2.2 + Math.sin(root.t * 0.5) * 2
        scale: 1 + root.beat * 0.07 + root.energy * 0.03

        // the ring of bars round it, mirrored so both sides match
        Repeater {
            model: 64
            Item {
                required property int index
                readonly property int m: index < 32 ? index : 63 - index
                readonly property real v: root.playing ? root.band(Math.floor(m * 24 / 32)) : 0.03 + 0.03 * Math.sin(root.t * 1.5 + index * 0.4)
                rotation: index * 360 / 64 - root.t * 6.5
                Rectangle {
                    width: Math.max(2, root.r * 0.018)
                    height: root.r * 0.03 + parent.v * root.r * 0.42
                    radius: width / 2
                    x: -width / 2
                    y: -root.r * 1.22 - height
                    color: Qt.tint(root.orange, Qt.alpha(root.hued("#ffd9b3"), parent.v * 0.6))
                    opacity: 0.3 + parent.v * 0.7
                }
            }
        }

        // rays: [angle°, length, width] (0–1 of r), a little uneven like the real one; each takes a band of its
        // own (the order mixes lows and highs round the circle)
        Repeater {
            model: [
                [0, 1.0, 0.22, 0], [29, 0.80, 0.20, 7], [61, 0.94, 0.21, 3], [90, 0.82, 0.20, 10],
                [119, 1.0, 0.22, 1], [150, 0.76, 0.19, 8], [179, 0.96, 0.21, 4], [209, 0.81, 0.20, 11],
                [238, 0.98, 0.22, 2], [269, 0.78, 0.19, 9], [300, 0.92, 0.21, 5], [331, 0.85, 0.20, 6]
            ]
            Item {
                id: ray
                required property var modelData
                required property int index
                readonly property real react: root.playing ? root.band(modelData[3] * 2) * 0.6 + root.band(modelData[3] * 2 + 1) * 0.4 : 0.035 * Math.sin(root.t * 1.3 + index * 1.7)
                readonly property real w: modelData[2] * root.r
                readonly property real len: root.r * modelData[1] * (1 + react * 0.3)
                rotation: modelData[0]
                Rectangle {
                    width: parent.w
                    height: parent.len + parent.w / 2
                    radius: width / 2
                    x: -width / 2
                    y: -parent.len
                    antialiasing: true
                    gradient: Gradient {
                        GradientStop {
                            position: 0
                            color: Qt.tint(root.hued("#e2805c"), Qt.alpha(root.hued("#ffd1a8"), Math.max(0, 0.4 * ray.react)))
                        }
                        GradientStop {
                            position: 1
                            color: root.hued("#d4714d")
                        }
                    }
                }
            }
        }
        HuedImage {                                   // hot core on the beat
            source: "dot.png"
            width: root.r * 0.9
            height: width
            x: -width / 2
            y: -height / 2
            opacity: root.beat * 0.55
        }
    }

    // the near half of the orbit, over the logo
    OrbitHalf {
        from: 0
        z: 8
    }

    // ── the little Claude, orbiting ──────────────────────────────────
    Item {
        id: moon
        readonly property real a: root.flow * 2 * Math.PI / 24     // once round every 24 s, quicker with music
        readonly property real px: Math.cos(a) * root.orx
        readonly property real py: Math.sin(a) * root.ory
        readonly property real tr: root.tilt * Math.PI / 180
        readonly property real near: (Math.sin(a) + 1) / 2         // 1 = in front, 0 = behind the logo
        readonly property real p: root.r * 0.05                     // one pixel
        x: root.cx + px * Math.cos(tr) - py * Math.sin(tr)
        y: root.cy + px * Math.sin(tr) + py * Math.cos(tr) + Math.sin(root.t * 3.1) * root.r * 0.02 - root.beat * root.r * 0.06
        z: Math.sin(a) > 0 ? 10 : 2
        scale: 0.62 + 0.38 * near
        rotation: Math.sin(a + Math.PI / 2) * 6

        HuedImage {
            source: "glow.png"
            width: moon.p * 26
            height: width
            x: -width / 2
            y: -height / 2
            opacity: 0.35 + root.energy * 0.3
        }

        // the mascot as pixels (18 × 5, tall pixels like the terminal's): body, arms, eyes, four legs
        Item {
            id: sprite
            readonly property real ph: moon.p * 1.7
            readonly property int step: Math.floor(root.t * (root.playing ? 7 : 4)) % 2
            readonly property bool blink: (root.t % 4.3) < 0.14
            readonly property color body: Qt.tint(root.orange, Qt.rgba(0.07, 0.03, 0.015, (1 - moon.near) * 0.5))   // in shade on the far side
            x: -9 * moon.p
            y: -2.5 * ph
            // [col, row, cols, rows, lifts with step 0/1 (-1: never)]: body, arms, legs
            readonly property var parts: [[3, 0, 12, 2, -1], [1, 2, 16, 1, -1], [3, 3, 12, 1, -1], [4, 4, 1, 1, 0], [6, 4, 1, 1, 1], [11, 4, 1, 1, 0], [13, 4, 1, 1, 1]]
            readonly property real o: moon.p * 0.45  // the dark outline, so it reads over the logo
            Repeater {
                model: sprite.parts
                Rectangle {
                    required property var modelData
                    readonly property real lift: modelData[4] === sprite.step ? 0.55 : 0
                    x: modelData[0] * moon.p - sprite.o
                    y: modelData[1] * sprite.ph - sprite.o
                    width: modelData[2] * moon.p + 2 * sprite.o
                    height: (modelData[3] - lift) * sprite.ph + 2 * sprite.o
                    color: root.hued("#1f0e07")
                }
            }
            Repeater {
                model: sprite.parts
                Rectangle {
                    required property var modelData
                    readonly property real lift: modelData[4] === sprite.step ? 0.55 : 0
                    x: modelData[0] * moon.p
                    y: modelData[1] * sprite.ph
                    width: modelData[2] * moon.p
                    height: (modelData[3] - lift) * sprite.ph + 0.5
                    color: sprite.body
                }
            }
            Repeater {                            // eyes
                model: [5, 12]
                Rectangle {
                    required property var modelData
                    x: modelData * moon.p
                    y: sprite.ph * (sprite.blink ? 1.75 : 1)
                    width: moon.p
                    height: sprite.ph * (sprite.blink ? 0.25 : 1)
                    color: root.hued("#1a0d08")
                }
            }
        }
    }
}
