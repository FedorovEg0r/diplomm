document.addEventListener('DOMContentLoaded', function() {
    const keywordList = document.getElementById('keyword-list');
    const keywordInput = document.getElementById('keyword-input');
    const addKeywordBtn = document.getElementById('add-keyword-btn');
    const keywordsField = document.getElementById('id_keywords');
    const existingKeywords = "{{ keywords|escapejs }}".split(',');

    existingKeywords.forEach(keyword => {
        if (keyword.trim()) {
            addKeywordToList(keyword.trim());
        }
    });

    addKeywordBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const keyword = keywordInput.value.trim();
        if (keyword) {
            addKeywordToList(keyword);
            keywordInput.value = '';
        }
    });

    function addKeywordToList(keyword) {
        const li = document.createElement('li');
        li.textContent = formatKeyword(keyword);
        const removeBtn = document.createElement('button');
        removeBtn.textContent = '×';
        removeBtn.classList.add('remove-btn');
        removeBtn.addEventListener('click', function() {
            li.remove();
            updateKeywordsField();
        });
        li.appendChild(removeBtn);
        keywordList.appendChild(li);
        updateKeywordsField();
    }

    function formatKeyword(keyword) {
        return keyword.length > 20 ? keyword.substring(0, 20) + '...' : keyword;
    }

    function updateKeywordsField() {
        const keywords = Array.from(keywordList.children).map(li => li.firstChild.textContent.replace('...', ''));
        keywordsField.value = keywords.join(',');
    }


    document.querySelector('form').addEventListener('submit', function() {
        document.getElementById('loader').style.visibility = 'visible';
    });
});

document.addEventListener("DOMContentLoaded", function() {
    const robot = document.querySelector('.robot');
    const keywordInput = document.querySelector('#keyword-input');
    const addKeywordButton = document.querySelector('#add-keyword-btn');

    keywordInput.addEventListener('input', function() {
        if (keywordInput.value.trim() !== "") {
            robot.classList.add('second-stage');
        } else {
            robot.classList.remove('second-stage');
        }
    });

    addKeywordButton.addEventListener('click', function() {
        robot.classList.remove('second-stage');
    });
});
