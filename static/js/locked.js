document.addEventListener("DOMContentLoaded", () => {
    const alertBox = document.getElementById("lockAlert");
    if (!alertBox) return;

    document.querySelectorAll(".locked-link").forEach((el) => {
    const show = () => {
        const level = el.dataset.level || "this";
        alertBox.textContent = `Locked: complete the previous level to unlock ${level}.`;
        alertBox.classList.remove("d-none");
        window.scrollTo({ top: 0, behavior: "smooth" });
        setTimeout(() => alertBox.classList.add("d-none"), 4000);
    };

    el.addEventListener("click", show);
    el.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") show();
    });
  });
});
