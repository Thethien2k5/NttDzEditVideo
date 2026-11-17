# Mẫu Code Khởi Tạo Đa Engine Chuẩn Hóa (Offline & Frame-Locked)

Mọi template dưới đây đều tuân thủ 3 nguyên tắc của `hyperframes-motion`:
1. Chỉ nạp thư viện cục bộ (`./gsap.min.js` + `./<engine>.min.js`).
2. Không sử dụng `requestAnimationFrame` tự do; mọi bước mô phỏng đều khóa theo `onFrameStep(time, dt)` của GSAP.
3. Hỗ trợ chuyển đổi nhanh giữa nền kín (`.mp4`) và nền trong suốt Alpha (`.webm` `yuva420p`).

---

## 1. Template `tsParticles` (Lớp phủ hạt không khí / Pháo giấy Alpha `.webm`)

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <style>
    html, body {
      width: 1920px; height: 1080px; margin: 0; overflow: hidden;
      background: transparent !important;
    }
    #tsparticles { width: 100%; height: 100%; }
  </style>
  <script src="./gsap.min.js"></script>
  <script src="./tsparticles.bundle.min.js"></script>
</head>
<body>
  <div id="tsparticles"></div>
  <script>
    const TOTAL_DURATION = 4.0;
    const FPS = 30;
    const DT = 1 / FPS;

    // Preset: Bụi ánh sáng điện ảnh (floating_dust) — có thể đổi sang tia lửa / pháo giấy
    const config = {
      autoPlay: false,
      background: { color: { value: "transparent" } },
      fpsLimit: FPS,
      particles: {
        number: { value: 65 },
        color: { value: ["#FFE600", "#38BDF8", "#FFFFFF"] },
        shape: { type: "circle" },
        opacity: { value: { min: 0.2, max: 0.85 } },
        size: { value: { min: 2, max: 6 } },
        move: {
          enable: true,
          speed: 1.8,
          direction: "top",
          outModes: { default: "out" }
        }
      }
    };

    (async () => {
      const container = await tsParticles.load({ id: "tsparticles", options: config });
      const tl = gsap.timeline({
        onUpdate: () => {
          if (container) container.draw(false);
        }
      });
      tl.fromTo("#tsparticles", { opacity: 0 }, { opacity: 1, duration: 0.4 })
        .to("#tsparticles", { duration: Math.max(0.2, TOTAL_DURATION - 0.8) })
        .to("#tsparticles", { opacity: 0, duration: 0.4 });
    })();
  </script>
</body>
</html>
```

---

## 2. Template `Three.js` (Sân khấu 3D / Mockup xoay `.mp4` hoặc `.webm` Alpha)

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <style>
    html, body {
      width: 1920px; height: 1080px; margin: 0; overflow: hidden;
      background: transparent !important; /* Đặt màu nền nếu xuất .mp4 */
    }
    canvas { display: block; width: 100%; height: 100%; }
  </style>
  <script src="./gsap.min.js"></script>
  <script src="./three.min.js"></script>
</head>
<body>
  <script>
    const WIDTH = 1920, HEIGHT = 1080, FPS = 30, TOTAL_DURATION = 4.0;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, WIDTH / HEIGHT, 0.1, 100);
    camera.position.set(0, 0.6, 5.5);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(WIDTH, HEIGHT);
    renderer.setClearColor(0x000000, 0); // Trong suốt hoàn toàn cho .webm
    document.body.appendChild(renderer.domElement);

    const ambient = new THREE.AmbientLight(0xffffff, 0.8);
    const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.8);
    dirLight.position.set(4, 6, 5);
    scene.add(ambient, dirLight);

    // Khối vật thể 3D mẫu (có thể thay bằng nhóm thẻ UI 3D)
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(2.2, 1.3, 0.25),
      new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.4, roughness: 0.25 })
    );
    scene.add(mesh);

    const tl = gsap.timeline({
      onUpdate: () => renderer.render(scene, camera)
    });

    tl.from(mesh.scale, { x: 0, y: 0, z: 0, duration: 0.6, ease: "back.out(1.6)" })
      .to(mesh.rotation, { y: Math.PI * 0.35, x: -0.15, duration: TOTAL_DURATION - 1.1, ease: "power1.inOut" }, 0.3)
      .to(mesh.scale, { x: 0, y: 0, z: 0, duration: 0.4, ease: "power2.in" }, TOTAL_DURATION - 0.4);
  </script>
</body>
</html>
```

---

## 3. Template `Matter.js` (Vật lý 2D: Thẻ từ khóa rơi & va chạm `.webm`)

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <style>
    html, body {
      width: 1920px; height: 1080px; margin: 0; overflow: hidden;
      background: transparent !important;
      font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    .tag {
      position: absolute; top: 0; left: 0;
      padding: 16px 32px; border-radius: 999px;
      background: #FFE600; color: #0F172A;
      font-size: 36px; font-weight: 800;
      will-change: transform;
    }
  </style>
  <script src="./gsap.min.js"></script>
  <script src="./matter.min.js"></script>
</head>
<body>
  <div id="tag-0" class="tag">TỐI ƯU HIỆU SUẤT</div>
  <div id="tag-1" class="tag" style="background:#38BDF8;">KHÔNG GIẬT LAG</div>
  <div id="tag-2" class="tag" style="background:#F43F5E;color:#fff;">TIẾT KIỆM VRAM</div>

  <script>
    const WIDTH = 1920, HEIGHT = 1080, FPS = 30, TOTAL_DURATION = 3.5;
    const DT_MS = 1000 / FPS;
    const { Engine, Bodies, Composite } = Matter;

    const engine = Engine.create();
    // Sàn đặt phía trên vùng an toàn phụ đề (80% chiều cao)
    const floor = Bodies.rectangle(WIDTH / 2, HEIGHT * 0.78, WIDTH, 40, { isStatic: true });
    Composite.add(engine.world, floor);

    const tags = [0, 1, 2].map((i) => {
      const el = document.getElementById(`tag-${i}`);
      const w = el.offsetWidth || 320;
      const h = el.offsetHeight || 72;
      const body = Bodies.rectangle(WIDTH * (0.35 + i * 0.15), -120 - i * 180, w, h, {
        restitution: 0.55,
        friction: 0.2,
        angle: (i - 1) * 0.12
      });
      Composite.add(engine.world, body);
      return { el, body, w, h };
    });

    const tl = gsap.timeline({
      onUpdate: () => {
        Engine.update(engine, DT_MS);
        for (const t of tags) {
          const { x, y } = t.body.position;
          t.el.style.transform = `translate(${x - t.w / 2}px, ${y - t.h / 2}px) rotate(${t.body.angle}rad)`;
        }
      }
    });

    tl.to({}, { duration: TOTAL_DURATION - 0.35 })
      .to(".tag", { opacity: 0, scale: 0.85, duration: 0.35, ease: "power2.in" });
  </script>
</body>
</html>
```

---

## 4. Template `p5.js` (Sóng âm thanh / Generative Visual `.webm` hoặc `.mp4`)

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <style>
    html, body {
      width: 1920px; height: 1080px; margin: 0; overflow: hidden;
      background: transparent !important;
    }
  </style>
  <script src="./gsap.min.js"></script>
  <script src="./p5.min.js"></script>
</head>
<body>
  <script>
    const WIDTH = 1920, HEIGHT = 1080, FPS = 30, TOTAL_DURATION = 4.0;
    let simTime = 0;

    new p5((p) => {
      p.setup = () => {
        const cnv = p.createCanvas(WIDTH, HEIGHT);
        cnv.style("background", "transparent");
        p.noLoop(); // Khóa vòng lặp tự do, chỉ vẽ khi GSAP gọi redraw()
      };

      p.draw = () => {
        p.clear();
        const bars = 48;
        const barW = 14;
        const gap = 12;
        const startX = (WIDTH - bars * (barW + gap)) / 2;
        const baseY = HEIGHT * 0.72; // Né vùng phụ đề dưới cùng

        p.noStroke();
        for (let i = 0; i < bars; i++) {
          const n = p.noise(i * 0.22, simTime * 4.5);
          const envelope = Math.sin((i / (bars - 1)) * Math.PI);
          const h = Math.max(12, n * 160 * envelope);
          p.fill(56, 189, 248, 220);
          p.rect(startX + i * (barW + gap), baseY - h / 2, barW, h, 8);
        }
      };

      const tl = gsap.timeline({
        onUpdate: () => {
          simTime = tl.time();
          p.redraw();
        }
      });
      tl.to({}, { duration: TOTAL_DURATION });
    });
  </script>
</body>
</html>
```
