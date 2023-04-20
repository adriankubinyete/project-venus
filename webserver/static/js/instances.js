function show_flash_messages() {
    var x = document.getElementById("flash-snack");
    x.className = "show";
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 2000);
}

window.addEventListener("load", () => {
show_flash_messages()
})