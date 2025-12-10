// Generic search autocomplete (gợi ý khi gõ trong các ô tìm kiếm)
// Sử dụng Bootstrap list-group để hiển thị gợi ý.

/**
 * Khởi tạo autocomplete cho input tìm kiếm.
 * @param {string} inputSelector - CSS selector của input.
 * @param {Object} options
 *  - endpoint: URL backend trả JSON gợi ý
 *  - param: tên query param gửi lên (mặc định: "term")
 *  - minChars: số ký tự tối thiểu mới bắt đầu gợi ý (mặc định: 2)
 *  - debounce: thời gian debounce (ms, mặc định: 250)
 *  - renderItem: function(item) => string HTML hiển thị
 *  - onSelect: function(item, input) khi chọn gợi ý
 */
function initSearchAutocomplete(inputSelector, options) {
    options = options || {};
    var endpoint = options.endpoint;
    if (!endpoint) return;

    var input = document.querySelector(inputSelector);
    if (!input) return;

    var paramName = options.param || 'term';
    var minChars = typeof options.minChars === 'number' ? options.minChars : 2;
    var debounceMs = typeof options.debounce === 'number' ? options.debounce : 250;

    // Tìm container bao quanh để đặt dropdown gợi ý
    var container = input.closest('.input-group');
    if (!container) {
        container = input.parentElement;
    }
    if (!container) return;

    // Đảm bảo container có position relative để dropdown định vị đúng
    if (!container.style.position) {
        container.style.position = 'relative';
    }

    // Tạo hộp gợi ý
    var suggestionsBox = document.createElement('div');
    suggestionsBox.className = 'list-group search-suggestions';
    suggestionsBox.style.position = 'absolute';
    suggestionsBox.style.top = '100%';
    suggestionsBox.style.left = '0';
    suggestionsBox.style.right = '0';
    suggestionsBox.style.zIndex = '1050';
    suggestionsBox.style.maxHeight = '260px';
    suggestionsBox.style.overflowY = 'auto';
    suggestionsBox.style.display = 'none';
    container.appendChild(suggestionsBox);

    var debounceTimer = null;

    function hideSuggestions() {
        suggestionsBox.style.display = 'none';
        suggestionsBox.innerHTML = '';
    }

    function showSuggestions(items) {
        suggestionsBox.innerHTML = '';
        if (!items || !items.length) {
            hideSuggestions();
            return;
        }
        items.forEach(function (item) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'list-group-item list-group-item-action py-1';
            if (typeof options.renderItem === 'function') {
                btn.innerHTML = options.renderItem(item);
            } else {
                var label = item.label || item.name || item.title || '';
                btn.textContent = label;
            }
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (typeof options.onSelect === 'function') {
                    options.onSelect(item, input);
                } else {
                    var value = item.value || item.name || item.label || '';
                    input.value = value;
                    if (input.form) input.form.submit();
                }
                hideSuggestions();
            });
            suggestionsBox.appendChild(btn);
        });
        suggestionsBox.style.display = 'block';
    }

    function fetchSuggestions(term) {
        var url = endpoint + '?' + encodeURIComponent(paramName) + '=' + encodeURIComponent(term);
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (!Array.isArray(data)) {
                    hideSuggestions();
                    return;
                }
                showSuggestions(data);
            })
            .catch(function () {
                hideSuggestions();
            });
    }

    input.addEventListener('input', function () {
        var term = (input.value || '').trim();
        if (term.length < minChars) {
            hideSuggestions();
            return;
        }
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }
        debounceTimer = setTimeout(function () {
            fetchSuggestions(term);
        }, debounceMs);
    });

    input.addEventListener('focus', function () {
        var term = (input.value || '').trim();
        if (term.length >= minChars && suggestionsBox.innerHTML) {
            suggestionsBox.style.display = 'block';
        }
    });

    // Ẩn khi click ra ngoài
    document.addEventListener('click', function (e) {
        if (!container.contains(e.target)) {
            hideSuggestions();
        }
    });
}


