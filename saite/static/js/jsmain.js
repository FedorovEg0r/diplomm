window.addEventListener('scroll', function() {
    var header = document.querySelector('header');
    var image2 = document.getElementById('image2');
    var heroText = document.querySelector('.hero-text');
    var scrollY = window.scrollY || window.pageYOffset;

    var fadeOutHeight = 100;
    var opacity = 1 - (scrollY / fadeOutHeight);
    opacity = opacity < 0 ? 0 : opacity;
    loader.style.visibility = 'hidden';
    heroText.style.opacity = opacity;

    if (scrollY > 0) {
        header.classList.add('shadow');
        image2.style.opacity = 1;
    } else {
        header.classList.remove('shadow');
        image2.style.opacity = 0;
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const steps = document.querySelectorAll('.step');
    const windowHeight = window.innerHeight;

    function checkVisibility() {
        for (let step of steps) {
            const rect = step.getBoundingClientRect();
            if (rect.top <= windowHeight * 0.8) {
                step.classList.add('visible');
            }
        }
    }

    window.addEventListener('scroll', checkVisibility);
    checkVisibility();
});
