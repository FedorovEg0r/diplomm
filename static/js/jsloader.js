function showLoader() {
    document.getElementById('loader').style.visibility = 'visible';
}

document.addEventListener('DOMContentLoaded', function() {
    var loader = document.getElementById('loader');

    function showLoader() {
        loader.style.visibility = 'visible';
    }

    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function(event) {
            if (!event.ctrlKey && !event.shiftKey && !event.metaKey && !link.target) {
                showLoader();
            }
        });
    });

    window.addEventListener('load', function() {
        loader.style.visibility = 'hidden';
    });
});
