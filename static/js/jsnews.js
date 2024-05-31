var lastScrollY = window.scrollY || window.pageYOffset;
var ticking = false;

function onScroll() {
    var header = document.querySelector('header');
    var heroText = document.getElementById('heroText');
    var image2 = document.getElementById('image2');
    var scrollY = window.scrollY || window.pageYOffset;
    var heroImageHeight = document.querySelector('.hero-image').offsetHeight;

    var startOffset = 20;
    var endOffset = heroImageHeight - 20 - heroText.offsetHeight;

    var newTop = startOffset + scrollY;
    if (newTop > endOffset) {
        newTop = endOffset;
    }

    heroText.style.top = newTop + 'px';

    var image2Start = 50;
    var image2End = 170;
    var image2Opacity = (scrollY - image2Start) / (image2End - image2Start);
    image2Opacity = Math.min(Math.max(image2Opacity, 0), 1);
    image2.style.opacity = image2Opacity;

    if (scrollY > 0) {
        header.classList.add('shadow');
    } else {
        header.classList.remove('shadow');
    }

    lastScrollY = scrollY;
    ticking = false;
}

function requestTick() {
    if (!ticking) {
        requestAnimationFrame(onScroll);
        ticking = true;
    }
}

window.addEventListener('scroll', requestTick);
document.addEventListener('DOMContentLoaded', onScroll);
        
document.addEventListener('DOMContentLoaded', function() {
    const addNewsBtn = document.getElementById('add-news-btn');
    const editorContainer = document.getElementById('editor-container');
    const saveNewsBtn = document.getElementById('save-news-btn');
    const newsContainer = document.getElementById('news-container');
    const newsTitle = document.getElementById('news-title');
    const loader = document.getElementById('loader');
    let editor;
    let editorVisible = false;

    const newsUrl = saveNewsBtn.dataset.url;

    addNewsBtn.addEventListener('click', function() {
        if (editorVisible) {
            if (editor) {
                editor.destroy()
                    .then(() => {
                        editorContainer.style.display = 'none';
                        editorVisible = false;
                    })
                    .catch(error => {
                        console.error(error);
                    });
            }
        } else {
            editorContainer.style.display = 'block';
            ClassicEditor
                .create(document.querySelector('#news-editor'), {
                    toolbar: ['bold', 'italic']
                })
                .then(newEditor => {
                    editor = newEditor;
                    editorVisible = true;
                })
                .catch(error => {
                    console.error(error);
                });
        }
    });

    saveNewsBtn.addEventListener('click', function() {
        if (editor) {
            const title = newsTitle.value;
            const content = editor.getData();

            loader.style.visibility = 'visible';

            fetch(newsUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                body: JSON.stringify({ title: title, content: content })
            })
            .then(response => response.json())
            .then(data => {
                loader.style.visibility = 'hidden';
                if (data.errors) {
                    console.error('Errors:', data.errors);
                } else {
                    const newsHtml = `
                        <div class="news-item" data-news-id="${data.id}">
                            <h2>${title}</h2>
                            <p>${new Date().toLocaleDateString()}</p>
                            <div>${content}</div>
                            <button class="delete-news-btn">Удалить</button>
                            <div class="delete-confirmation">
                                Вы уверены, что хотите удалить?
                                <button class="confirm-delete-btn">Удалить</button>
                                <button class="cancel-delete-btn">Отмена</button>
                            </div>
                            <hr>
                        </div>
                    `;

                    newsContainer.insertAdjacentHTML('afterbegin', newsHtml);
                    editor.destroy()
                        .then(() => {
                            editorContainer.style.display = 'none';
                            newsTitle.value = '';
                            editorVisible = false;
                        })
                        .catch(error => {
                            console.error(error);
                        });
                }
            })
            .catch(error => {
                loader.style.visibility = 'hidden';
                console.error('Error:', error);
            });
        }
    });

    newsContainer.addEventListener('click', function(event) {
        if (event.target.classList.contains('delete-news-btn')) {
            const newsItem = event.target.closest('.news-item');
            const deleteBtn = newsItem.querySelector('.delete-news-btn');
            const confirmationDiv = newsItem.querySelector('.delete-confirmation');
            deleteBtn.style.display = 'none';
            confirmationDiv.style.display = 'block';
        } else if (event.target.classList.contains('confirm-delete-btn')) {
            const newsItem = event.target.closest('.news-item');
            const newsId = newsItem.dataset.newsId;

            loader.style.visibility = 'visible';

            fetch(`/delete_news/${newsId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}'
                }
            })
            .then(response => {
                loader.style.visibility = 'hidden';
                if (response.ok) {
                    newsItem.remove();
                } else {
                    console.error('Failed to delete news item');
                }
            })
            .catch(error => {
                loader.style.visibility = 'hidden';
                console.error('Error:', error);
            });
        } else if (event.target.classList.contains('cancel-delete-btn')) {
            const newsItem = event.target.closest('.news-item');
            const deleteBtn = newsItem.querySelector('.delete-news-btn');
            const confirmationDiv = newsItem.querySelector('.delete-confirmation');
            confirmationDiv.style.display = 'none';
            deleteBtn.style.display = 'block';
        }
    });
});



