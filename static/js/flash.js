document.addEventListener("DOMContentLoaded", () => {
    const area = document.getElementById("flashArea");
    if (!area) return;

    setTimeout(() => {
        area.querySelectorAll(".alert").forEach((a) => a.remove());
    }, 4000);
});
