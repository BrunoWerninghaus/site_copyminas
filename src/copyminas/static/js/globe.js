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
    rotationSpeed: 0.00075,
};

const mounts = document.querySelectorAll("[data-globe-mount]");

for (const mount of mounts) {
    if (mount.dataset.globeMount === "intro") {
        createIntroGlobe(mount).catch((error) => {
            console.error("Copy Minas globe:", error);

            const status = document.querySelector("[data-globe-status]");
            if (status) {
                status.textContent = "Globo indisponível";
            }
        });
    }
}

async function createIntroGlobe(mount) {
    const [world, minas] = await Promise.all([
        loadJSON(WORLD_URL),
        loadJSON(MINAS_URL),
    ]);

    const mask = createGeoMask(world, minas);
    const points = buildPointSets(mask);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);

    camera.position.set(0, 0, 11.2);

    const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
    });

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.65));
    renderer.setClearColor(0x000000, 0);

    mount.appendChild(renderer.domElement);

    const earth = new THREE.Group();
    earth.rotation.z = THREE.MathUtils.degToRad(-23.4);
    scene.add(earth);

    const oceanMaterial = new THREE.PointsMaterial({
        color: COLORS.ocean,
        size: CONFIG.pointSize * 0.62,
        transparent: true,
        opacity: 0.24,
        depthWrite: false,
    });

    const landMaterial = new THREE.PointsMaterial({
        color: COLORS.land,
        size: CONFIG.pointSize,
        transparent: true,
        opacity: 0.94,
    });

    const brazilMaterial = new THREE.PointsMaterial({
        color: COLORS.brazil,
        size: CONFIG.pointSize * 1.38,
        transparent: true,
        opacity: 1,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
    });

    const minasMaterial = new THREE.PointsMaterial({
        color: COLORS.minas,
        size: CONFIG.pointSize * 2.25,
        transparent: true,
        opacity: 1,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
    });

    const minasGlowMaterial = new THREE.PointsMaterial({
        color: COLORS.minas,
        size: CONFIG.pointSize * 5.5,
        transparent: true,
        opacity: 0.18,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
    });

    earth.add(
        new THREE.Points(createGeometry(points.ocean), oceanMaterial),
        new THREE.Points(createGeometry(points.land), landMaterial),
        new THREE.Points(createGeometry(points.brazil), brazilMaterial),
        new THREE.Points(createGeometry(points.minas), minasMaterial),
        new THREE.Points(createGeometry(points.minas), minasGlowMaterial),
    );

    const clock = new THREE.Clock();

    const resize = () => {
        const width = Math.max(mount.clientWidth, 1);
        const height = Math.max(mount.clientHeight, 1);

        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();

        if (window.matchMedia("(max-width: 820px)").matches) {
            earth.position.x = 0;
            earth.position.y = 1.45;
            camera.position.z = 11.7;
        } else {
            earth.position.x = -2.25;
            earth.position.y = 0;
            camera.position.z = 10.8;
        }
    };

    resize();
    window.addEventListener("resize", resize, { passive: true });

    const host = mount.closest(".intro-globe");
    if (host) {
        host.classList.add("intro-globe--ready");
    }

    const animate = () => {
        const elapsed = clock.getElapsedTime();
        const pulse = (Math.sin(elapsed * 2.3) + 1) / 2;

        earth.rotation.y += CONFIG.rotationSpeed;
        minasMaterial.size = CONFIG.pointSize * (2.05 + pulse * 0.45);
        minasGlowMaterial.size = CONFIG.pointSize * (4.7 + pulse * 2.0);
        minasGlowMaterial.opacity = 0.10 + pulse * 0.20;

        renderer.render(scene, camera);
        requestAnimationFrame(animate);
    };

    animate();
}

async function loadJSON(url) {
    const response = await fetch(url, {
        headers: {
            Accept: "application/json, application/geo+json",
        },
    });

    if (!response.ok) {
        throw new Error(`Falha ao carregar dados geográficos: ${response.status}`);
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

function createGeometry(positions) {
    const geometry = new THREE.BufferGeometry();

    geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(positions, 3),
    );

    geometry.computeBoundingSphere();

    return geometry;
}
