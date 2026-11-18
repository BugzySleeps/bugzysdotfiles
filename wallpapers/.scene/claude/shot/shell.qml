import QtQuick
import Quickshell
import Quickshell.Io

// Renders scene.qml once and saves it: the still claude.png (and test frames). Run by ../shot.sh.
//   SHOT=<png>  where to save · W/H  size · FLOW  where the moon is · PLAY=1  fake some music
ShellRoot {
    FloatingWindow {
        id: win
        implicitWidth: Number(Quickshell.env("W") || 1920)
        implicitHeight: Number(Quickshell.env("H") || 1080)
        color: "black"

        QtObject {
            id: feed
            readonly property bool play: Quickshell.env("PLAY") === "1"
            property real time: Number(Quickshell.env("FLOW") || 9.5)
            property real flow: time
            property real energy: play ? 0.6 : 0
            property real beat: play ? 0.75 : 0
            property bool playing: play
            property var accent: Quickshell.env("ACCENT") || null
            property var bands: play ? Array.from({ length: 30 }, (_, i) => Math.max(0, 0.95 - i * 0.03 + 0.25 * Math.sin(i * 1.9))) : []
        }
        // Quickshell won't load QML from outside its config folder, so (like liquid) read it and build it from text
        Item {                                   // its own size, whatever size the window ends up (it's grabbed off screen)
            id: scene
            width: Number(Quickshell.env("W") || 1920)
            height: Number(Quickshell.env("H") || 1080)
        }
        FileView {
            path: Quickshell.env("SCENE") + "/scene.qml"
            onLoaded: {
                const o = Qt.createQmlObject(text(), scene, "file://" + Quickshell.env("SCENE") + "/scene.qml");
                o.anchors.fill = scene;
                o.feed = feed;
            }
        }
        Timer {
            interval: 1500
            running: true
            onTriggered: scene.grabToImage(r => {
                r.saveToFile(Quickshell.env("SHOT"));
                Qt.quit();
            })
        }
    }
}
