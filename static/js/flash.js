/*waiting until the page content is fully loaded before excuting the script*/
document.addEventListener("DOMContentLoaded", () => {
    /* selecting the flash message container and exits if it does not exist*/
    const area = document.getElementById("flashArea");

    if (!area) return;

    setTimeout(() => {
    /* automatically removes all alert messages inside the container after 4 second to keep the UI clean*/
        area.querySelectorAll(".alert").forEach((a) => a.remove());
    }, 4000);
});
