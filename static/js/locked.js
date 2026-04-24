/*waiting until the page is fully loaded before running the script*/
document.addEventListener("DOMContentLoaded", () => {
    /* selecting the alert box element and stops ecution if it does not exist*/
    const alertBox = document.getElementById("lockAlert");
    
    if (!alertBox) return;
    /*selects all locked links and prepares to attach event handlers to them*/
    document.querySelectorAll(".locked-link").forEach((el) => {
    /*defining the function to display a message explaining that level locked,
      updates the alerts text dynamically, shows the alert, scrolls to the top smoothly, and hides ot after 4 second */
        const show = () => {
        const level = el.dataset.level || "this";
        alertBox.textContent = `Locked: complete the previous level to unlock ${level}.`;
        alertBox.classList.remove("d-none");
        window.scrollTo({ top: 0, behavior: "smooth" });
        setTimeout(() => alertBox.classList.add("d-none"), 4000);
    };

    /* adding click event listener to trigger the locked message when the user clicks the element */
    el.addEventListener("click", show);
    /*adding the keyboard accessibility, allowing the message to appear when the user presses enter or space on a locked element*/
    el.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") show();
    });
  });
});
