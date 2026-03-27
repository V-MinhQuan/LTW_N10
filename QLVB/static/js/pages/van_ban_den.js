function openVBD(id) {
    document.getElementById(id).style.display = 'flex';
}
function closeVBD(id) {
    document.getElementById(id).style.display = 'none';
}

// Close on overlay click
window.onclick = function(event) {
    if (event.target.classList.contains('vbd-popup-overlay')) {
        event.target.style.display = "none";
    }
}
