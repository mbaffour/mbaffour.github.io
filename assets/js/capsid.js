/* capsid.js — the hero's 3D phage N4 head (three.js r128, assets/vendor/three.min.js).
 *
 * An icosahedral capsid built the way capsids are: each of the 20 triangular
 * faces is tiled with capsomers (hexamers), with a five-fold pentamer at each of
 * the 12 vertices, then a short podovirus tail at one vertex. Capsomers are two
 * InstancedMeshes, so the whole head is three draw calls.
 *
 * It turns slowly, leans toward the pointer, and the capsomers nearest the
 * pointer lift off the shell, so it reads as a physical object you can touch.
 * stage.js drives window.capsid.scroll(p) as the hero scrolls away.
 * Paused off screen; reduced motion gets one still frame.
 */
(function () {
    var host = document.getElementById('capsid');
    if (!host || typeof THREE === 'undefined') return;
    var canvas = document.createElement('canvas');
    canvas.className = 'capsid-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    var renderer;
    try {
        renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
    } catch (e) { return; }   // no WebGL: the static picture in the markup stays
    host.appendChild(canvas);
    host.classList.add('is-live');
    var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(28, 1, 0.1, 50);
    camera.position.set(0, -0.15, 8.4);

    /* ---------- light: a warm key, then the three Kente colours as rims ---------- */
    scene.add(new THREE.HemisphereLight(0x8a7a66, 0x120c08, 0.4));
    var key = new THREE.DirectionalLight(0xfff1d6, 1.3); key.position.set(-3, 4, 5); scene.add(key);
    var rim = new THREE.DirectionalLight(0xf7c52b, 3.0); rim.position.set(4, 1.5, -3); scene.add(rim);
    var rim2 = new THREE.DirectionalLight(0xe8304e, 2.4); rim2.position.set(-4, 2.5, -2); scene.add(rim2);
    var fill = new THREE.PointLight(0x19b85a, 1.6, 20); fill.position.set(-2.5, -3, 3); scene.add(fill);

    /* ---------- geometry: capsomer positions on the 20 flat faces ---------- */
    var ico = new THREE.IcosahedronGeometry(1, 0), pos = ico.attributes.position, N = 6;
    var pts = [], seen = {};
    function addPt(v, five) {
        var k = v.x.toFixed(3) + ',' + v.y.toFixed(3) + ',' + v.z.toFixed(3);
        if (seen[k] !== undefined) { if (five) pts[seen[k]].five = true; return; }
        seen[k] = pts.length; pts.push({ p: v.clone(), five: !!five });
    }
    for (var f = 0; f < pos.count; f += 3) {
        var A = new THREE.Vector3().fromBufferAttribute(pos, f), B = new THREE.Vector3().fromBufferAttribute(pos, f + 1), C = new THREE.Vector3().fromBufferAttribute(pos, f + 2);
        for (var i = 0; i <= N; i++) for (var j = 0; j <= N - i; j++) {
            var k2 = N - i - j, v = new THREE.Vector3().addScaledVector(A, i / N).addScaledVector(B, j / N).addScaledVector(C, k2 / N);
            addPt(v, i === N || j === N || k2 === N);
        }
    }
    // a slightly domed icosahedron, as real heads read in cryo-EM
    pts.forEach(function (q) {
        var r = q.p.length(), dome = q.p.clone().normalize().multiplyScalar(1.0);
        q.p.lerp(dome, 0.35);
        q.dir = q.p.clone().normalize();
        q.base = q.p.clone();
        q.ph = Math.random() * 6.28;
    });
    var head = new THREE.Group();
    scene.add(head);
    var hexGeo = new THREE.CylinderGeometry(0.083, 0.094, 0.06, 6, 1);
    hexGeo.rotateX(Math.PI / 2);   // axis along +z, so lookAt points it outward
    var pentGeo = new THREE.CylinderGeometry(0.078, 0.09, 0.085, 5, 1);
    pentGeo.rotateX(Math.PI / 2);
    var hexMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.55, metalness: 0.35 });
    var pentMat = new THREE.MeshStandardMaterial({ color: 0xf4c430, roughness: 0.3, metalness: 0.75, emissive: 0x4a3200, emissiveIntensity: 0.35 });
    var hexes = pts.filter(function (q) { return !q.five; }), pents = pts.filter(function (q) { return q.five; });
    var hexMesh = new THREE.InstancedMesh(hexGeo, hexMat, hexes.length);
    var pentMesh = new THREE.InstancedMesh(pentGeo, pentMat, pents.length);
    head.add(hexMesh); head.add(pentMesh);
    // Kente weave: a dark head with three woven bands, green, gold and red,
    // running round it by latitude, so the colours turn with the spin.
    // (Colours are converted to linear, as the renderer outputs sRGB.)
    function lin(h) { return new THREE.Color(h).convertSRGBToLinear(); }
    var DARK = lin(0x2a2119), HOT = lin(0xffd23f), col = new THREE.Color();
    var BANDS = [[-0.5, lin(0x16a352)], [0.0, lin(0xe0a91c)], [0.5, lin(0xd42a45)]];
    hexes.forEach(function (q) {
        q.col = DARK;
        BANDS.forEach(function (b) { if (Math.abs(q.dir.y - b[0]) < 0.1) q.col = b[1]; });
    });
    // the shell under the capsomers, so the gaps read as depth, not holes
    var core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.85, 3), new THREE.MeshStandardMaterial({ color: 0x0e0a07, roughness: 0.9, metalness: 0.1 }));
    head.add(core);

    /* ---------- the tail: N4 is a podophage, so short and stubby ----------
       A stub well under the head's radius, a collar, and twelve short
       appendages folded close round it. No long tail fibres, no baseplate. */
    var tailDir = pents.reduce(function (best, q) { return q.p.y < best.p.y ? q : best; }, pents[0]).dir.clone();
    var tail = new THREE.Group();
    var neck = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.19, 0.24, 12), new THREE.MeshStandardMaterial({ color: 0x2a231b, roughness: 0.5, metalness: 0.5 }));
    neck.position.y = -1.08;
    var plate = new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.22, 0.09, 12), pentMat);
    plate.position.y = -1.23;
    tail.add(neck); tail.add(plate);
    var fiberMat = new THREE.MeshStandardMaterial({ color: 0x8a7444, roughness: 0.5, metalness: 0.5 });
    for (i = 0; i < 12; i++) {
        var a = i / 12 * Math.PI * 2;
        var curve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(Math.cos(a) * 0.2, -1.2, Math.sin(a) * 0.2),
            new THREE.Vector3(Math.cos(a) * 0.29, -1.26, Math.sin(a) * 0.29),
            new THREE.Vector3(Math.cos(a) * 0.32, -1.37, Math.sin(a) * 0.32)
        ]);
        tail.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 8, 0.016, 6, false), fiberMat));
    }
    tail.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), tailDir);
    head.add(tail);
    head.rotation.set(0.35, 0.6, 0.12);

    /* ---------- instance update: breathing, plus the pointer lifting capsomers ---------- */
    var m4 = new THREE.Matrix4(), q4 = new THREE.Quaternion(), s3 = new THREE.Vector3(), p3 = new THREE.Vector3(), up = new THREE.Vector3(0, 0, 1);
    var touch = new THREE.Vector3(9, 9, 9), touchK = 0;
    function place(mesh, list, t) {
        var tint = mesh === hexMesh;
        for (var n = 0; n < list.length; n++) {
            var q = list[n];
            var wave = Math.sin(t * 1.3 + q.base.y * 5 + q.ph * 0.3) * 0.012;
            var d2 = q.base.distanceToSquared(touch), lift = touchK * Math.exp(-d2 / 0.09);
            if (tint) { col.copy(q.col).lerp(HOT, Math.min(1, lift * 1.3)); mesh.setColorAt(n, col); }
            p3.copy(q.base).addScaledVector(q.dir, wave + lift * 0.22);
            q4.setFromUnitVectors(up, q.dir);
            s3.set(1 + lift * 0.25, 1 + lift * 0.25, 1 + lift * 2.2);
            m4.compose(p3, q4, s3);
            mesh.setMatrixAt(n, m4);
        }
        mesh.instanceMatrix.needsUpdate = true;
        if (tint && mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    }

    /* ---------- sizing, pointer, scroll ---------- */
    function size() {
        var w = host.clientWidth || 400, h = host.clientHeight || 400;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    }
    size();
    window.addEventListener('resize', size);
    var mx = 0, my = 0, tmx = 0, tmy = 0, over = false;
    var ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), sphere = new THREE.Sphere(new THREE.Vector3(), 1.02), hit = new THREE.Vector3(), inv = new THREE.Matrix4();
    window.addEventListener('pointermove', function (e) {
        tmx = e.clientX / window.innerWidth - 0.5; tmy = e.clientY / window.innerHeight - 0.5;
        var b = canvas.getBoundingClientRect();
        ndc.set((e.clientX - b.left) / b.width * 2 - 1, -((e.clientY - b.top) / b.height) * 2 + 1);
        over = Math.abs(ndc.x) <= 1 && Math.abs(ndc.y) <= 1;
    }, { passive: true });
    // a tap (or click) on the head lifts the capsomers under it for a moment,
    // with a light tick on phones that can give one
    var poke = 0;
    host.addEventListener('pointerdown', function (e) {
        var b = canvas.getBoundingClientRect();
        ndc.set((e.clientX - b.left) / b.width * 2 - 1, -((e.clientY - b.top) / b.height) * 2 + 1);
        ray.setFromCamera(ndc, camera);
        sphere.center.copy(head.position);
        if (!ray.ray.intersectSphere(sphere, hit)) return;
        poke = 0.7;
        if (e.pointerType === 'touch' && navigator.vibrate) { try { navigator.vibrate(12); } catch (err) {} }
        if (!running) { touchK = 1; inv.copy(head.matrixWorld).invert(); touch.copy(hit).applyMatrix4(inv); place(hexMesh, hexes, 0); place(pentMesh, pents, 0); renderer.render(scene, camera); }
    });
    var scrollP = 0;
    window.capsid = { scroll: function (p) { scrollP = p; } };

    var t0 = performance.now(), last = t0, spin = 0, running = false, visible = true;
    function frame(now) {
        if (!running) return;
        var dt = Math.min(0.05, (now - last) / 1000); last = now;
        var t = (now - t0) / 1000;
        mx += (tmx - mx) * 0.05; my += (tmy - my) * 0.05;
        spin += dt * (0.16 + scrollP * 1.4);
        head.rotation.y = 0.6 + spin + mx * 0.6;
        head.rotation.x = 0.35 + my * 0.45 + Math.sin(t * 0.4) * 0.05;
        head.position.y = Math.sin(t * 0.7) * 0.05 + scrollP * 0.9;
        var sc = 1 - scrollP * 0.35;
        head.scale.set(sc, sc, sc);
        // where the pointer meets the shell, in the head's own frame
        var hitNow = false;
        poke = Math.max(0, poke - dt);
        if (over || poke > 0) {
            ray.setFromCamera(ndc, camera);
            sphere.center.copy(head.position); sphere.radius = 1.02 * sc;
            if (ray.ray.intersectSphere(sphere, hit)) {
                inv.copy(head.matrixWorld).invert();
                touch.copy(hit).applyMatrix4(inv);
                hitNow = true;
            }
        }
        touchK += ((hitNow ? 1 : 0) - touchK) * 0.08;
        place(hexMesh, hexes, t); place(pentMesh, pents, t);
        renderer.render(scene, camera);
        requestAnimationFrame(frame);
    }
    function setRun() {
        var go = visible && !document.hidden && !reduce;
        if (go && !running) { running = true; last = performance.now(); requestAnimationFrame(frame); }
        else if (!go) running = false;
    }
    place(hexMesh, hexes, 0); place(pentMesh, pents, 0);
    head.updateMatrixWorld();
    renderer.render(scene, camera);
    if (reduce) return;
    if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; setRun(); }).observe(host);
    document.addEventListener('visibilitychange', setRun);
    setRun();
})();
