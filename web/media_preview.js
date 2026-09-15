import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function getEagleAudioResourceURL(audioRef) {
    const params = new URLSearchParams();
    params.set("filename", audioRef?.filename ?? "");
    params.set("type", audioRef?.type ?? "output");
    params.set("subfolder", audioRef?.subfolder ?? "");
    params.set("rand", String(Math.random()));
    return api.apiURL(`/view?${params.toString()}`);
}

app.registerExtension({
    name: "EagleBridge.AudioPlayer",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "EagleSaveAudio") return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        const originalOnExecuted = nodeType.prototype.onExecuted;

        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);

            const audio = document.createElement("audio");
            audio.controls = true;
            audio.preload = "metadata";
            audio.classList.add("comfy-audio");
            audio.setAttribute("name", "media");
            audio.style.width = "100%";
            audio.style.display = "none";

            const audioWidget = this.addDOMWidget(
                "eagleAudioUI",
                "audioUI",
                audio,
                {
                    serialize: false,
                    hideOnZoom: false,
                    getHeight: () => (audio.style.display === "none" ? 0 : 54),
                    getMinHeight: () => (audio.style.display === "none" ? 0 : 54),
                }
            );

            audioWidget.serialize = false;
            audioWidget.options ??= {};
            audioWidget.options.serialize = false;

            this._eagleAudioElement = audio;
            this._eagleAudioWidget = audioWidget;

            return result;
        };

        nodeType.prototype.onExecuted = function (output) {
            originalOnExecuted?.apply(this, arguments);

            const audio = this._eagleAudioElement;
            if (!audio) return;

            const audios = output?.audio;
            if (!audios?.length) {
                audio.pause?.();
                audio.removeAttribute("src");
                audio.load?.();
                audio.style.display = "none";
                this.setDirtyCanvas?.(true, true);
                return;
            }

            const ref = audios[0];
            if (!ref?.filename) return;

            audio.src = getEagleAudioResourceURL(ref);
            audio.style.display = "block";
            audio.load();

            try {
                const computed = this.computeSize?.();
                if (computed && this.size) {
                    this.setSize?.([
                        Math.max(this.size[0], computed[0]),
                        Math.max(this.size[1], computed[1]),
                    ]);
                }
            } catch (_) {}

            this.setDirtyCanvas?.(true, true);
        };
    },
});


function getEagleVideoResourceURL(videoRef) {
    const params = new URLSearchParams();
    params.set("filename", videoRef?.filename ?? "");
    params.set("type", videoRef?.type ?? "output");
    params.set("subfolder", videoRef?.subfolder ?? "");
    params.set("rand", String(Math.random()));
    return api.apiURL(`/view?${params.toString()}`);
}

app.registerExtension({
    name: "EagleBridge.VideoPlayer",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "EagleSaveVideo") return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        const originalOnExecuted = nodeType.prototype.onExecuted;

        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);

            const video = document.createElement("video");
            video.controls = true;
            video.preload = "metadata";
            video.playsInline = true;
            video.style.width = "100%";
            video.style.maxHeight = "320px";
            video.style.display = "none";
            video.style.background = "#000";

            const videoWidget = this.addDOMWidget(
                "eagleVideoUI",
                "videoUI",
                video,
                {
                    serialize: false,
                    hideOnZoom: false,
                    getHeight: () => (video.style.display === "none" ? 0 : 240),
                    getMinHeight: () => (video.style.display === "none" ? 0 : 180),
                }
            );

            videoWidget.serialize = false;
            videoWidget.options ??= {};
            videoWidget.options.serialize = false;

            this._eagleVideoElement = video;
            this._eagleVideoWidget = videoWidget;

            return result;
        };

        nodeType.prototype.onExecuted = function (output) {
            originalOnExecuted?.apply(this, arguments);

            const video = this._eagleVideoElement;
            if (!video) return;

            const videos = output?.video;
            if (!videos?.length) {
                video.pause?.();
                video.removeAttribute("src");
                video.load?.();
                video.style.display = "none";
                this.setDirtyCanvas?.(true, true);
                return;
            }

            const ref = videos[0];
            if (!ref?.filename) return;

            video.src = getEagleVideoResourceURL(ref);
            video.style.display = "block";
            video.load();

            try {
                const computed = this.computeSize?.();
                if (computed && this.size) {
                    this.setSize?.([
                        Math.max(this.size[0], computed[0]),
                        Math.max(this.size[1], computed[1]),
                    ]);
                }
            } catch (_) {}

            this.setDirtyCanvas?.(true, true);
        };
    },
});
