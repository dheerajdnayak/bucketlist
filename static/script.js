gsap.registerPlugin(ScrollTrigger);

// Cursor
const dot = document.getElementById("cursorDot");
document.addEventListener("mousemove", (e) => {
  gsap.to(dot, { x: e.clientX, y: e.clientY, duration: 0.1, ease: "power2.out" });
});
document.querySelectorAll("a, .btn").forEach((el) => {
  el.addEventListener("mouseenter", () => dot.classList.add("cursor-dot--large"));
  el.addEventListener("mouseleave", () => dot.classList.remove("cursor-dot--large"));
});

// Scroll progress
gsap.to("#scrollProgress", {
  scaleX: 1,
  ease: "none",
  scrollTrigger: { trigger: document.body, start: "top top", end: "bottom bottom", scrub: true }
});

// Reveal on scroll (simple)
function reveal(selector, fromVars, toVars) {
  const els = document.querySelectorAll(selector);
  els.forEach(el => {
    gsap.set(el, { opacity: 0 });
    ScrollTrigger.create({
      trigger: el,
      start: "top 85%",
      onEnter: () => gsap.fromTo(el, { opacity: 0, ...fromVars }, { opacity: 1, duration: 0.8, ease: "power3.out", ...toVars })
    });
  });
}
reveal(".hero h1", { y: 40 }, { y: 0 });
reveal(".hero p", { y: 30 }, { y: 0, delay: 0.1 });
reveal(".hero-actions", { y: 30 }, { y: 0, delay: 0.2 });
