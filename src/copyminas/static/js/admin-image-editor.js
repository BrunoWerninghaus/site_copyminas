"use strict";

(() => {
    const root = document.querySelector("[data-image-editor]");
    if (!root) return;

    const canvas = root.querySelector("[data-editor-canvas]");
    const ctx = canvas.getContext("2d", {alpha: true});
    const frame = root.querySelector("[data-editor-frame]");
    const status = root.querySelector("[data-editor-status]");
    const saveButton = root.querySelector("[data-editor-save]");
    const csrf = root.querySelector("[data-image-editor-csrf]");

    const zoomInput = root.querySelector("[data-editor-zoom]");
    const zoomValue = root.querySelector("[data-editor-zoom-value]");
    const toleranceInput = root.querySelector("[data-editor-tolerance]");
    const toleranceValue = root.querySelector("[data-editor-tolerance-value]");
    const backgroundInput = root.querySelector("[data-editor-background]");
    const originalButton = root.querySelector("[data-editor-original]");

    const originalCanvas = document.createElement("canvas");
    const workingCanvas = document.createElement("canvas");

    const state = {
        ready: false,
        zoom: 1,
        offsetX: 0,
        offsetY: 0,
        rotation: 0,
        flipX: 1,
        flipY: 1,
        background: "transparent",
        showOriginal: false,
        dragging: false,
        pointerX: 0,
        pointerY: 0,
    };

    const setStatus = (message, kind = "") => {
        status.textContent = message;
        status.dataset.kind = kind;
    };

    const sourceForRender = (forceEdited = false) => {
        if (!forceEdited && state.showOriginal) return originalCanvas;
        return workingCanvas;
    };

    const draw = (forceEdited = false) => {
        if (!state.ready) return;

        const source = sourceForRender(forceEdited);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (state.background === "white") {
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        const quarterTurn = Math.abs(state.rotation % 180) === 90;
        const rotatedWidth = quarterTurn ? source.height : source.width;
        const rotatedHeight = quarterTurn ? source.width : source.height;
        const fitScale = Math.min(
            canvas.width / rotatedWidth,
            canvas.height / rotatedHeight
        ) * 0.86;
        const scale = fitScale * state.zoom;

        ctx.save();
        ctx.translate(
            canvas.width / 2 + state.offsetX,
            canvas.height / 2 + state.offsetY
        );
        ctx.rotate((state.rotation * Math.PI) / 180);
        ctx.scale(scale * state.flipX, scale * state.flipY);
        ctx.drawImage(source, -source.width / 2, -source.height / 2);
        ctx.restore();
    };

    const resetPlacement = () => {
        state.zoom = 1;
        state.offsetX = 0;
        state.offsetY = 0;
        zoomInput.value = "100";
        zoomValue.textContent = "100%";
        draw();
    };

    const restoreWorkingImage = () => {
        workingCanvas.width = originalCanvas.width;
        workingCanvas.height = originalCanvas.height;
        const working = workingCanvas.getContext("2d", {willReadFrequently: true});
        working.clearRect(0, 0, workingCanvas.width, workingCanvas.height);
        working.drawImage(originalCanvas, 0, 0);
        state.showOriginal = false;
        originalButton.textContent = "Ver original";
        draw();
        setStatus("Imagem original restaurada para edição.");
    };

    const removeBackground = () => {
        if (!state.ready) return;

        setStatus("Removendo fundo…");

        window.requestAnimationFrame(() => {
            const width = originalCanvas.width;
            const height = originalCanvas.height;
            const original = originalCanvas.getContext("2d", {willReadFrequently: true});
            const source = original.getImageData(0, 0, width, height);
            const output = new Uint8ClampedArray(source.data);
            const visited = new Uint8Array(width * height);
            const queue = new Int32Array(width * height);
            const tolerance = Number(toleranceInput.value || 55);
            const limit = tolerance * tolerance * 3;

            const pixelColor = (pixelIndex) => {
                const offset = pixelIndex * 4;
                return [
                    source.data[offset],
                    source.data[offset + 1],
                    source.data[offset + 2],
                ];
            };

            const references = [
                pixelColor(0),
                pixelColor(width - 1),
                pixelColor((height - 1) * width),
                pixelColor(height * width - 1),
            ];

            const matchesBackground = (pixelIndex) => {
                const offset = pixelIndex * 4;
                if (source.data[offset + 3] === 0) return true;

                const r = source.data[offset];
                const g = source.data[offset + 1];
                const b = source.data[offset + 2];

                for (const reference of references) {
                    const dr = r - reference[0];
                    const dg = g - reference[1];
                    const db = b - reference[2];
                    if ((dr * dr + dg * dg + db * db) <= limit) {
                        return true;
                    }
                }
                return false;
            };

            let head = 0;
            let tail = 0;

            const enqueue = (index) => {
                if (index < 0 || index >= visited.length || visited[index]) return;
                visited[index] = 1;
                if (!matchesBackground(index)) return;
                queue[tail++] = index;
            };

            for (let x = 0; x < width; x += 1) {
                enqueue(x);
                enqueue((height - 1) * width + x);
            }
            for (let y = 0; y < height; y += 1) {
                enqueue(y * width);
                enqueue(y * width + width - 1);
            }

            while (head < tail) {
                const index = queue[head++];
                output[index * 4 + 3] = 0;

                const x = index % width;
                const y = Math.floor(index / width);
                if (x > 0) enqueue(index - 1);
                if (x < width - 1) enqueue(index + 1);
                if (y > 0) enqueue(index - width);
                if (y < height - 1) enqueue(index + width);
            }

            workingCanvas.width = width;
            workingCanvas.height = height;
            const working = workingCanvas.getContext("2d", {willReadFrequently: true});
            working.putImageData(new ImageData(output, width, height), 0, 0);

            state.showOriginal = false;
            originalButton.textContent = "Ver original";
            draw();
            setStatus(
                tail > 0
                    ? "Fundo removido. Ajuste a sensibilidade e repita se necessário."
                    : "Nenhum fundo semelhante às bordas foi detectado.",
                tail > 0 ? "success" : "warning"
            );
        });
    };

    const prepareForCatalog = () => {
        state.background = "transparent";
        backgroundInput.value = "transparent";
        state.rotation = 0;
        state.flipX = 1;
        state.flipY = 1;
        resetPlacement();
        removeBackground();
    };

    const image = new Image();
    image.onload = () => {
        originalCanvas.width = image.naturalWidth;
        originalCanvas.height = image.naturalHeight;
        originalCanvas.getContext("2d", {willReadFrequently: true}).drawImage(image, 0, 0);

        workingCanvas.width = image.naturalWidth;
        workingCanvas.height = image.naturalHeight;
        workingCanvas.getContext("2d", {willReadFrequently: true}).drawImage(image, 0, 0);

        state.ready = true;
        saveButton.disabled = false;
        draw();
        setStatus("Imagem pronta para edição.", "success");
    };
    image.onerror = () => {
        setStatus("Não foi possível carregar a imagem deste produto.", "error");
    };
    image.src = root.dataset.sourceUrl;

    root.querySelector("[data-editor-fit]").addEventListener("click", resetPlacement);
    root.querySelector("[data-editor-remove-bg]").addEventListener("click", removeBackground);
    root.querySelector("[data-editor-restore]").addEventListener("click", restoreWorkingImage);
    root.querySelector("[data-editor-prepare]").addEventListener("click", prepareForCatalog);

    root.querySelectorAll("[data-editor-rotate]").forEach((button) => {
        button.addEventListener("click", () => {
            state.rotation = (state.rotation + Number(button.dataset.editorRotate)) % 360;
            resetPlacement();
        });
    });

    root.querySelectorAll("[data-editor-flip]").forEach((button) => {
        button.addEventListener("click", () => {
            if (button.dataset.editorFlip === "x") state.flipX *= -1;
            if (button.dataset.editorFlip === "y") state.flipY *= -1;
            draw();
        });
    });

    originalButton.addEventListener("click", () => {
        state.showOriginal = !state.showOriginal;
        originalButton.textContent = state.showOriginal ? "Ver edição" : "Ver original";
        draw();
        setStatus(
            state.showOriginal
                ? "Visualizando a imagem original preservada."
                : "Visualizando a versão em edição."
        );
    });

    backgroundInput.addEventListener("change", () => {
        state.background = backgroundInput.value;
        draw();
    });

    zoomInput.addEventListener("input", () => {
        state.zoom = Number(zoomInput.value) / 100;
        zoomValue.textContent = `${zoomInput.value}%`;
        draw();
    });

    toleranceInput.addEventListener("input", () => {
        toleranceValue.textContent = toleranceInput.value;
    });

    const pointerPosition = (event) => {
        const rect = canvas.getBoundingClientRect();
        return {
            x: (event.clientX - rect.left) * (canvas.width / rect.width),
            y: (event.clientY - rect.top) * (canvas.height / rect.height),
        };
    };

    canvas.addEventListener("pointerdown", (event) => {
        if (!state.ready) return;
        const point = pointerPosition(event);
        state.dragging = true;
        state.pointerX = point.x;
        state.pointerY = point.y;
        canvas.setPointerCapture(event.pointerId);
        frame.classList.add("is-dragging");
    });

    canvas.addEventListener("pointermove", (event) => {
        if (!state.dragging) return;
        const point = pointerPosition(event);
        state.offsetX += point.x - state.pointerX;
        state.offsetY += point.y - state.pointerY;
        state.pointerX = point.x;
        state.pointerY = point.y;
        draw();
    });

    const stopDragging = (event) => {
        if (!state.dragging) return;
        state.dragging = false;
        frame.classList.remove("is-dragging");
        if (event.pointerId !== undefined && canvas.hasPointerCapture(event.pointerId)) {
            canvas.releasePointerCapture(event.pointerId);
        }
    };

    canvas.addEventListener("pointerup", stopDragging);
    canvas.addEventListener("pointercancel", stopDragging);

    canvas.addEventListener("wheel", (event) => {
        if (!state.ready) return;
        event.preventDefault();

        const delta = event.deltaY < 0 ? 5 : -5;
        const next = Math.max(25, Math.min(250, Number(zoomInput.value) + delta));
        zoomInput.value = String(next);
        state.zoom = next / 100;
        zoomValue.textContent = `${next}%`;
        draw();
    }, {passive: false});

    saveButton.addEventListener("click", async () => {
        if (!state.ready || saveButton.disabled) return;

        saveButton.disabled = true;
        setStatus("Salvando versão editada…");

        const previousOriginalState = state.showOriginal;
        state.showOriginal = false;
        draw(true);
        const imageData = canvas.toDataURL("image/png");
        state.showOriginal = previousOriginalState;
        draw();

        const form = new FormData();
        form.append("csrf_token", csrf.value);
        form.append("image_data", imageData);

        try {
            const response = await fetch(root.dataset.saveUrl, {
                method: "POST",
                body: form,
                credentials: "same-origin",
                headers: {"Accept": "application/json"},
            });
            const payload = await response.json();

            if (!response.ok || !payload.ok) {
                throw new Error(payload.error || "Não foi possível salvar a imagem.");
            }

            setStatus("Imagem salva. Retornando ao produto…", "success");
            window.location.assign(payload.redirect);
        } catch (error) {
            setStatus(error.message || "Não foi possível salvar a imagem.", "error");
            saveButton.disabled = false;
        }
    });
})();
