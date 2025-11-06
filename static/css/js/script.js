const image = document.querySelector('.draggable');

images.forEach(img=> {
    img.addEventListener('mousedown', startDrag);
    img.addEventListener('mouseup', stopDrag);
    img.addEventListener('mousemove', drag);
});

let active = null;
let offsetX, offsetY;

function startDrag(e) {
    active = e.target;
    offsetX = e.clientX - active.offsetLeft;
    offsetY = e.clientY - active.offsetTop;
}

function drag(e) {
    if (!active) return;
    active.style.left = `${e.clientX - offsetX}px`;
    active.style.top = `${e.clientY - offsetY}px`;
}

function stopDrag() {
    active = null;
}

const draggables = document.querySelectorAll('.draggable');

draggables.forEach(img => {
    img.addEventListener('mousedown', onMouseDown);

function onMouseDown(e) {
    e.preventDefault();
    let shiftX = e.clientX - img.getBoundingClientRect().left;
    let shiftY = e.clientY - img.getBoundingClientRect().top;
}

document.addEventListener('mousemove', onMouseMove);

img.addEventListener('mouseup', function mouseUp() {
    document.removeEventListener('mousemove', onMouseMove);
    img.removeEventListener('mouseup', mouseUp);
});

img.ondragstart = () => false;
});



