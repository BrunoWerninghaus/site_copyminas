import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js";

const WORLD_URL =
    "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json";

const MINAS_URL =
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/31?formato=application/vnd.geo+json&qualidade=intermediaria";

const COLORS = {
    ocean: 0x244154,
    land: 0xdfe4e8,
    brazil: 0xf01d27,
    minas: 0xffd447,
    eloi: 0x1595ff,
};

const MASK_COLORS = {
    land: "#dfe4e8",
    brazil: "#f01d27",
    minas: "#ffd447",
};

const CONFIG = {
    radius: 4.75,
    pointCount: 130000,
    pointSize: 0.027,
    rotationSpeed: 0.00072,
};

const preparedData = prepareGlobeData();

const introMount = document.querySelector('[data-globe-mount="intro"]');
const previewMount = document.querySelector('[data-globe-mount="home-preview"]');
const fullscreenMount = document.querySelector('[data-globe-mount="fullscreen"]');

if (introMount) {
    preparedData
        .then((data) => createGlobe(introMount, data, {
            mode: "intro",
            interactive: false,
            autoRotate: true,
        }))
        .catch((error) => {
            console.error("Copy Minas globe:", error);

            const status = document.querySelector("[data-globe-status]");
            if (status) {
                status.textContent = "Globo indisponível";
            }
        });
}

if (previewMount) {
    preparedData
        .then((data) => createGlobe(previewMount, data, {
            mode: "preview",
            interactive: false,
            autoRotate: false,
        }))
        .then((controller) => {
            previewMount.closest(".globe-card")?.classList.add("globe-card--ready");
            observeGlobeVisibility(previewMount, controller);
        })
        .catch((error) => {
            console.error("Copy Minas globe preview:", error);
        });
}

setupFullscreenGlobe();

async function prepareGlobeData() {
    const [world, minas] = await Promise.all([
        loadJSON(WORLD_URL),
        loadJSON(MINAS_URL),
    ]);

    const mask = createGeoMask(world, minas);

    return buildPointSets(mask);
}

async function createGlobe(mount, points, options) {
    const location = readLocation(mount);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);

    camera.position.set(0, 0, options.mode === "fullscreen" ? 12.2 : 11.2);

    const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
    });

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.65));
    renderer.setClearColor(0x000000, 0);

    mount.replaceChildren(renderer.domElement);

    const earth = new THREE.Group();
    scene.add(earth);

    const materials = createMaterials();

    earth.add(
        new THREE.Points(createGeometry(points.ocean), materials.ocean),
        new THREE.Points(createGeometry(points.land), materials.land),
        new THREE.Points(createGeometry(points.brazil), materials.brazil),
        new THREE.Points(createGeometry(points.minas), materials.minas),
        new THREE.Points(createGeometry(points.minas), materials.minasGlow),
    );

    const marker = createLocationMarker(location);
    earth.add(marker.group);

    focusGlobeOnLocation(earth, location);

    const pinLabel = createPinLabel(mount, location.label);
    const clock = new THREE.Clock();

    let dragging = false;
    let dragged = false;
    let previousX = 0;
    let previousY = 0;
    let active = true;

    const resize = () => {
        const width = Math.max(mount.clientWidth, 1);
        const height = Math.max(mount.clientHeight, 1);

        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();

        if (options.mode === "intro") {
            if (window.matchMedia("(max-width: 820px)").matches) {
                earth.position.x = 0;
                earth.position.y = 1.4;
                camera.position.z = 11.7;
            } else {
                earth.position.x = -2.25;
                earth.position.y = 0;
                camera.position.z = 10.8;
            }
        } else {
            earth.position.set(0, 0, 0);
        }
    };

    resize();

    if ("ResizeObserver" in window) {
        const resizeObserver = new ResizeObserver(() => {
            requestAnimationFrame(resize);
        });
        resizeObserver.observe(mount);
    } else {
        window.addEventListener("resize", resize, { passive: true });
    }

    if (options.interactive) {
        const raycaster = new THREE.Raycaster();
        const pointer = new THREE.Vector2();

        const markerHit = (event) => {
            setRayFromPointer(event, renderer.domElement, camera, raycaster, pointer);
            return raycaster.intersectObject(marker.core, false).length > 0;
        };

        const updatePinCursor = (event) => {
            renderer.domElement.style.cursor = markerHit(event) ? "pointer" : "grab";
        };

        renderer.domElement.addEventListener("pointerdown", (event) => {
            dragging = true;
            dragged = false;
            previousX = event.clientX;
            previousY = event.clientY;
            renderer.domElement.setPointerCapture(event.pointerId);
        });

        renderer.domElement.addEventListener("pointermove", (event) => {
            if (!dragging) {
                updatePinCursor(event);
                return;
            }

            const deltaX = event.clientX - previousX;
            const deltaY = event.clientY - previousY;

            if (Math.abs(deltaX) + Math.abs(deltaY) > 2) {
                dragged = true;
            }

            earth.rotation.y += deltaX * 0.006;
            earth.rotation.x = THREE.MathUtils.clamp(
                earth.rotation.x + deltaY * 0.004,
                -0.75,
                0.75,
            );

            previousX = event.clientX;
            previousY = event.clientY;
        });

        renderer.domElement.addEventListener("pointerup", (event) => {
            dragging = false;

            if (!dragged && markerHit(event)) {
                openMaps(location.mapsUrl);
            }
        });

        renderer.domElement.addEventListener(
            "wheel",
            (event) => {
                event.preventDefault();
                camera.position.z = THREE.MathUtils.clamp(
                    camera.position.z + event.deltaY * 0.008,
                    7.2,
                    18,
                );
            },
            { passive: false },
        );
    }

    if (options.mode === "intro") {
        mount.closest(".intro-globe")?.classList.add("intro-globe--ready");
    }

    const stop = () => {
        active = false;
    };

    const start = () => {
        if (active) {
            return;
        }

        active = true;
        animate();
    };

    const animate = () => {
        if (!active) {
            return;
        }

        const elapsed = clock.getElapsedTime();
        const pulse = (Math.sin(elapsed * 2.4) + 1) / 2;

        if (options.autoRotate && !dragging) {
            earth.rotation.y += CONFIG.rotationSpeed;
        }

        materials.minas.size = CONFIG.pointSize * (2.05 + pulse * 0.45);
        materials.minasGlow.size = CONFIG.pointSize * (4.7 + pulse * 2.0);
        materials.minasGlow.opacity = 0.10 + pulse * 0.20;

        marker.core.scale.setScalar(0.92 + pulse * 0.16);
        marker.glow.scale.setScalar(0.82 + pulse * 0.55);
        marker.glow.material.opacity = 0.16 + pulse * 0.30;

        renderer.render(scene, camera);
        updatePinLabel(pinLabel, marker.core, earth, camera, renderer);

        requestAnimationFrame(animate);
    };

    animate();

    return {
        resize,
        start,
        stop,
    };
}

function setupFullscreenGlobe() {
    const dialog = document.querySelector("[data-globe-dialog]");
    const openButton = document.querySelector("[data-globe-open]");
    const closeButton = document.querySelector("[data-globe-close]");

    if (!dialog || !openButton || !closeButton || !fullscreenMount) {
        return;
    }

    let globeController = null;
    let creating = null;

    const ensureGlobe = () => {
        if (globeController) {
            globeController.start();
            globeController.resize();
            return Promise.resolve(globeController);
        }

        if (!creating) {
            creating = preparedData
                .then((data) => createGlobe(fullscreenMount, data, {
                    mode: "fullscreen",
                    interactive: true,
                    autoRotate: false,
                }))
                .then((controller) => {
                    globeController = controller;
                    requestAnimationFrame(controller.resize);
                    return controller;
                });
        }

        return creating;
    };

    openButton.addEventListener("click", () => {
        dialog.showModal();
        document.documentElement.classList.add("globe-dialog-open");
        ensureGlobe().catch((error) => {
            console.error("Copy Minas fullscreen globe:", error);
        });
    });

    closeButton.addEventListener("click", () => {
        dialog.close();
    });

    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) {
            dialog.close();
        }
    });

    dialog.addEventListener("close", () => {
        document.documentElement.classList.remove("globe-dialog-open");
        globeController?.stop();
    });
}

function focusGlobeOnLocation(earth, location) {
    if (!Number.isFinite(location.lat) || !Number.isFinite(location.lon)) {
        return;
    }

    const locationDirection = latLonToXYZ(
        location.lat,
        location.lon,
        1,
    ).normalize();

    const cameraFacingDirection = new THREE.Vector3(0, 0, 1);

    earth.quaternion.setFromUnitVectors(
        locationDirection,
        cameraFacingDirection,
    );
}

function observeGlobeVisibility(mount, controller) {
    if (!("IntersectionObserver" in window)) {
        return;
    }

    const observer = new IntersectionObserver(
        ([entry]) => {
            if (entry.isIntersecting) {
                controller.start();
            } else {
                controller.stop();
            }
        },
        {
            rootMargin: "180px 0px",
            threshold: 0.01,
        },
    );

    observer.observe(mount);
}

function createMaterials() {
    return {
        ocean: new THREE.PointsMaterial({
            color: COLORS.ocean,
            size: CONFIG.pointSize * 0.62,
            transparent: true,
            opacity: 0.24,
            depthWrite: false,
        }),
        land: new THREE.PointsMaterial({
            color: COLORS.land,
            size: CONFIG.pointSize,
            transparent: true,
            opacity: 0.94,
        }),
        brazil: new THREE.PointsMaterial({
            color: COLORS.brazil,
            size: CONFIG.pointSize * 1.38,
            transparent: true,
            opacity: 1,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
        }),
        minas: new THREE.PointsMaterial({
            color: COLORS.minas,
            size: CONFIG.pointSize * 2.25,
            transparent: true,
            opacity: 1,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
        }),
        minasGlow: new THREE.PointsMaterial({
            color: COLORS.minas,
            size: CONFIG.pointSize * 5.5,
            transparent: true,
            opacity: 0.18,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
        }),
    };
}

function createLocationMarker(location) {
    const group = new THREE.Group();
    const position = latLonToXYZ(
        location.lat,
        location.lon,
        CONFIG.radius + 0.16,
    );

    group.position.copy(position);

    const core = new THREE.Mesh(
        new THREE.SphereGeometry(0.105, 20, 20),
        new THREE.MeshBasicMaterial({
            color: COLORS.eloi,
        }),
    );

    const glow = new THREE.Mesh(
        new THREE.SphereGeometry(0.23, 20, 20),
        new THREE.MeshBasicMaterial({
            color: COLORS.eloi,
            transparent: true,
            opacity: 0.30,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
        }),
    );

    group.add(glow, core);

    return {
        group,
        core,
        glow,
    };
}

function createPinLabel(mount, label) {
    if (!label || mount.dataset.globeMount === "intro") {
        return null;
    }

    const node = document.createElement("span");
    node.className = "globe-pin-label";
    node.textContent = label;
    mount.appendChild(node);

    return node;
}

function updatePinLabel(label, pin, earth, camera, renderer) {
    if (!label) {
        return;
    }

    const pinPosition = new THREE.Vector3();
    const earthCenter = new THREE.Vector3();

    pin.getWorldPosition(pinPosition);
    earth.getWorldPosition(earthCenter);

    const normal = pinPosition.clone().sub(earthCenter).normalize();
    const towardCamera = camera.position.clone().sub(pinPosition).normalize();
    const visible = normal.dot(towardCamera) > 0.08;

    if (!visible) {
        label.hidden = true;
        return;
    }

    label.hidden = false;

    const projected = pinPosition.clone().project(camera);
    const rect = renderer.domElement.getBoundingClientRect();
    const rawX = (projected.x * 0.5 + 0.5) * rect.width + 14;
    const rawY = (-projected.y * 0.5 + 0.5) * rect.height - label.offsetHeight / 2;
    const clamped = clampPinLabelPosition(
        rawX,
        rawY,
        label.offsetWidth,
        label.offsetHeight,
        rect.width,
        rect.height,
    );

    label.style.left = clamped.x + "px";
    label.style.top = clamped.y + "px";
}

function clampPinLabelPosition(
    x,
    y,
    labelWidth,
    labelHeight,
    mountWidth,
    mountHeight,
) {
    const inset = 12;
    const maxX = Math.max(inset, mountWidth - labelWidth - inset);
    const maxY = Math.max(inset, mountHeight - labelHeight - inset);

    return {
        x: THREE.MathUtils.clamp(x, inset, maxX),
        y: THREE.MathUtils.clamp(y, inset, maxY),
    };
}

function setRayFromPointer(event, canvas, camera, raycaster, pointer) {
    const rect = canvas.getBoundingClientRect();

    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(pointer, camera);
}

function openMaps(url) {
    if (!url) {
        return;
    }

    window.open(url, "_blank", "noopener,noreferrer");
}

function readLocation(mount) {
    return {
        lat: Number.parseFloat(mount.dataset.locationLat),
        lon: Number.parseFloat(mount.dataset.locationLon),
        label: mount.dataset.locationLabel || "Elói Mendes",
        mapsUrl: mount.dataset.mapsUrl || "",
    };
}

async function loadJSON(url) {
    const response = await fetch(url, {
        headers: {
            Accept: "application/json, application/geo+json",
        },
    });

    if (!response.ok) {
        throw new Error("Falha ao carregar dados geográficos: " + response.status);
    }

    return response.json();
}

function createGeoMask(world, minasPayload) {
    const width = 2048;
    const height = 1024;
    const canvas = document.createElement("canvas");

    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext("2d", {
        willReadFrequently: true,
    });

    context.clearRect(0, 0, width, height);

    for (const feature of world.features ?? []) {
        const name = normalizeCountryName(feature.properties);
        const color = name === "brazil" || name === "brasil"
            ? MASK_COLORS.brazil
            : MASK_COLORS.land;

        drawFeature(context, feature, color, width, height);
    }

    const minasFeature = normalizeFeature(minasPayload);

    if (minasFeature) {
        drawFeature(
            context,
            minasFeature,
            MASK_COLORS.minas,
            width,
            height,
        );
    }

    return {
        width,
        height,
        pixels: context.getImageData(0, 0, width, height).data,
    };
}

function normalizeCountryName(properties = {}) {
    return String(
        properties.name ??
        properties.NAME ??
        properties.ADMIN ??
        properties.name_long ??
        ""
    )
        .trim()
        .toLowerCase();
}

function normalizeFeature(payload) {
    if (!payload) {
        return null;
    }

    if (payload.type === "Feature") {
        return payload;
    }

    if (payload.type === "FeatureCollection") {
        return payload.features?.[0] ?? null;
    }

    if (payload.type === "Polygon" || payload.type === "MultiPolygon") {
        return {
            type: "Feature",
            properties: {},
            geometry: payload,
        };
    }

    return null;
}

function drawFeature(context, feature, color, width, height) {
    const geometry = feature?.geometry;

    if (!geometry) {
        return;
    }

    const polygons = geometry.type === "Polygon"
        ? [geometry.coordinates]
        : geometry.type === "MultiPolygon"
            ? geometry.coordinates
            : [];

    context.fillStyle = color;

    for (const polygon of polygons) {
        context.beginPath();

        for (const ring of polygon) {
            ring.forEach(([lon, lat], index) => {
                const { x, y } = project(lon, lat, width, height);

                if (index === 0) {
                    context.moveTo(x, y);
                } else {
                    context.lineTo(x, y);
                }
            });

            context.closePath();
        }

        context.fill("evenodd");
    }
}

function project(lon, lat, width, height) {
    return {
        x: ((lon + 180) / 360) * width,
        y: ((90 - lat) / 180) * height,
    };
}

function buildPointSets(mask) {
    const sets = {
        ocean: [],
        land: [],
        brazil: [],
        minas: [],
    };

    for (let index = 0; index < CONFIG.pointCount; index += 1) {
        const point = fibonacciPoint(index, CONFIG.pointCount);
        const { lat, lon } = xyzToLatLon(point.x, point.y, point.z);

        const sampleX = Math.min(
            mask.width - 1,
            Math.max(0, Math.floor(((lon + 180) / 360) * mask.width)),
        );

        const sampleY = Math.min(
            mask.height - 1,
            Math.max(0, Math.floor(((90 - lat) / 180) * mask.height)),
        );

        const offset = (sampleY * mask.width + sampleX) * 4;

        const red = mask.pixels[offset];
        const green = mask.pixels[offset + 1];
        const blue = mask.pixels[offset + 2];
        const alpha = mask.pixels[offset + 3];

        let target = sets.ocean;
        let radius = CONFIG.radius;

        if (alpha > 40) {
            radius += 0.025;

            if (red > 220 && green < 90 && blue < 110) {
                target = sets.brazil;
            } else if (red > 220 && green > 150 && blue < 120) {
                target = sets.minas;
                radius += 0.045;
            } else {
                target = sets.land;
            }
        }

        target.push(
            point.x * radius,
            point.y * radius,
            point.z * radius,
        );
    }

    return sets;
}

function fibonacciPoint(index, total) {
    const goldenAngle = Math.PI * (3 - Math.sqrt(5));
    const y = 1 - (index / (total - 1)) * 2;
    const horizontalRadius = Math.sqrt(Math.max(0, 1 - y * y));
    const theta = goldenAngle * index;

    return {
        x: Math.cos(theta) * horizontalRadius,
        y,
        z: Math.sin(theta) * horizontalRadius,
    };
}

function xyzToLatLon(x, y, z) {
    const lat = Math.asin(y) * 180 / Math.PI;
    const lon = -Math.atan2(z, x) * 180 / Math.PI;

    return { lat, lon };
}

function latLonToXYZ(lat, lon, radius) {
    const latRadians = THREE.MathUtils.degToRad(lat);
    const lonRadians = THREE.MathUtils.degToRad(lon);
    const horizontalRadius = Math.cos(latRadians);

    return new THREE.Vector3(
        Math.cos(lonRadians) * horizontalRadius * radius,
        Math.sin(latRadians) * radius,
        -Math.sin(lonRadians) * horizontalRadius * radius,
    );
}

function createGeometry(positions) {
    const geometry = new THREE.BufferGeometry();

    geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(positions, 3),
    );

    geometry.computeBoundingSphere();

    return geometry;
}
