// Flashcards study mode: click to flip, ← → to navigate.
(function () {
  const area = document.getElementById("flashcard-area");
  if (!area) return;
  const cards = Array.from(area.querySelectorAll(".flashcard"));
  const total = cards.length;
  if (total === 0) return;
  const counter = document.getElementById("counter");
  const fill = document.getElementById("progress-fill");
  let i = 0;

  function show(idx) {
    cards.forEach((c, k) => (c.hidden = k !== idx));
    const card = cards[idx];
    card.querySelector(".front").hidden = false;
    card.querySelector(".back").hidden = true;
    counter.textContent = `${idx + 1} / ${total}`;
    if (fill) fill.style.width = `${((idx + 1) / total) * 100}%`;
  }

  area.addEventListener("click", (e) => {
    const card = e.target.closest(".flashcard");
    if (!card) return;
    const front = card.querySelector(".front");
    const back = card.querySelector(".back");
    if (front.hidden) { front.hidden = false; back.hidden = true; }
    else { front.hidden = true; back.hidden = false; }
  });

  document.getElementById("prev-btn").onclick = () => { i = (i - 1 + total) % total; show(i); };
  document.getElementById("next-btn").onclick = () => { i = (i + 1) % total; show(i); };
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { i = (i - 1 + total) % total; show(i); }
    if (e.key === "ArrowRight") { i = (i + 1) % total; show(i); }
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); cards[i].click(); }
  });

  show(0);
})();