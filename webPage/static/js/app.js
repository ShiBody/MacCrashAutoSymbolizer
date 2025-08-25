// MacCrash Auto Symbolizer Web App - GitHub Style
// 全局变量
let currentLang = 'zh';
let currentActiveTab = 'text';
let currentOutputTab = 'result';
let isProcessing = false;

// 语言配置
const languages = {
    zh: {
        code: 'zh',
        name: '中文',
        flag: '🇨🇳'
    },
    en: {
        code: 'en', 
        name: 'English',
        flag: '🇺🇸'
    }
};

// DOM 元素
let symbolizeForm, symbolizeBtn, clearBtn;
let outputTabButtons, outputContents;
let fileUploadArea, crashFile, fileInfo, fileName, removeFileBtn;
let symbolizeResult, logsResult, progressIndicator;
let copyResultBtn, downloadResultBtn, messageContainer;
let langSwitch, langDropdown, currentLangSpan;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    initializeEventListeners();
    initializeLanguage();
    initializeFormValidation();
    
    // 设置默认的输入方式
    switchInputMethod('text');
});

// 初始化DOM元素
function initializeElements() {
    symbolizeForm = document.getElementById('symbolizeForm');
    symbolizeBtn = document.getElementById('symbolizeBtn');
    clearBtn = document.getElementById('clearBtn');
    
    outputTabButtons = document.querySelectorAll('.btn-tab');
    outputContents = document.querySelectorAll('.output-content');
    
    fileUploadArea = document.getElementById('fileUploadArea');
    crashFile = document.getElementById('crash_file');
    fileInfo = document.getElementById('fileInfo');
    fileName = document.getElementById('fileName');
    removeFileBtn = document.getElementById('removeFile');
    
    symbolizeResult = document.getElementById('symbolizeResult');
    logsResult = document.getElementById('logsResult');
    progressIndicator = document.getElementById('progressIndicator');
    
    copyResultBtn = document.getElementById('copyResultBtn');
    downloadResultBtn = document.getElementById('downloadResultBtn');
    messageContainer = document.getElementById('messageContainer');
    
    langSwitch = document.getElementById('langSwitch');
    langDropdown = document.getElementById('langDropdown');
    currentLangSpan = document.getElementById('currentLang');
}

// 初始化事件监听器
function initializeEventListeners() {
    // 表单提交
    if (symbolizeForm) {
        symbolizeForm.addEventListener('submit', handleFormSubmit);
    }
    
    // 清空按钮
    if (clearBtn) {
        clearBtn.addEventListener('click', clearResults);
    }
    
    // 输入方式切换
    const inputMethodRadios = document.querySelectorAll('input[name="inputMethod"]');
    inputMethodRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            switchInputMethod(e.target.value);
        });
    });
    
    // 输出选项卡
    outputTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            switchOutputTab(button.dataset.tab);
        });
    });
    
    // 文件上传相关
    if (fileUploadArea) {
        // 为了避免与隐藏的file input冲突，我们直接监听file-upload-content
        const uploadContent = fileUploadArea.querySelector('.file-upload-content');
        if (uploadContent) {
            uploadContent.addEventListener('click', (e) => {
                e.preventDefault();
                if (crashFile) {
                    crashFile.click();
                }
            });
        }
        
        // 保持原有的拖拽功能
        fileUploadArea.addEventListener('dragover', handleDragOver);
        fileUploadArea.addEventListener('dragleave', handleDragLeave);
        fileUploadArea.addEventListener('drop', handleFileDrop);
        
        // 确保删除按钮正常工作
        const removeBtn = fileUploadArea.querySelector('.btn-remove');
        if (removeBtn) {
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeFile();
            });
        }
    }
    
    if (crashFile) {
        crashFile.addEventListener('change', handleFileSelect);
    } else {
        console.error('File input element not found during initialization');
    }
    
    // 删除按钮的事件绑定已在上面的fileUploadArea中处理
    
    // 复制和下载按钮
    if (copyResultBtn) {
        copyResultBtn.addEventListener('click', copyResult);
    }
    
    if (downloadResultBtn) {
        downloadResultBtn.addEventListener('click', downloadResult);
    }
    
    // 语言切换
    if (langSwitch) {
        langSwitch.addEventListener('click', toggleLanguageDropdown);
    }
    
    // 语言选项
    const langOptions = document.querySelectorAll('.lang-option');
    langOptions.forEach(option => {
        option.addEventListener('click', (e) => {
            e.preventDefault();
            switchLanguage(option.dataset.lang);
        });
    });
    
    // 点击其他地方关闭语言下拉菜单
    document.addEventListener('click', (e) => {
        if (langSwitch && langDropdown && 
            !langSwitch.contains(e.target) && 
            !langDropdown.contains(e.target)) {
            closeLangDropdown();
        }
    });
}

// 语言切换功能
function initializeLanguage() {
    // 从localStorage读取保存的语言设置
    const savedLang = localStorage.getItem('app-language') || 'zh';
    
    // 初始化输出框的占位内容
    initializeOutputPlaceholders(savedLang);
    
    switchLanguage(savedLang);
}

// 初始化输出框占位内容
function initializeOutputPlaceholders(lang) {
    const symbolizeResult = document.getElementById('symbolizeResult');
    const logsResult = document.getElementById('logsResult');
    
    if (symbolizeResult) {
        const emptyText = symbolizeResult.getAttribute(`data-empty-${lang}`);
        if (emptyText) {
            symbolizeResult.textContent = emptyText;
        }
    }
    
    if (logsResult) {
        const emptyText = logsResult.getAttribute(`data-empty-${lang}`);
        if (emptyText) {
            logsResult.textContent = emptyText;
        }
    }
}

// 检查是否为占位内容
function isPlaceholderContent(text) {
    const placeholderKeywords = [
        '等待开始符号化', 'Waiting for symbolization',
        '暂无日志信息', 'No log information',
        'Click', '点击', 'Start Symbolization', 'available'
    ];
    
    return placeholderKeywords.some(keyword => text.includes(keyword));
}

// 强制更新输出框内容
function forceUpdateOutputBoxes(lang) {
    const outputBoxes = document.querySelectorAll('.output-code');
    
    outputBoxes.forEach(box => {
        const currentText = box.textContent.trim();
        const emptyText = box.getAttribute(`data-empty-${lang}`);
        
        // 如果是空的或者是占位内容，强制更新
        if ((!currentText || isPlaceholderContent(currentText)) && emptyText) {
            box.textContent = emptyText;
        }
    });
}

function toggleLanguageDropdown() {
    if (langDropdown) {
        langDropdown.classList.toggle('show');
    }
}

function closeLangDropdown() {
    langDropdown.classList.remove('show');
}

function switchLanguage(lang) {
    if (!languages[lang]) return;
    
    currentLang = lang;
    localStorage.setItem('app-language', lang);
    
    // 更新HTML lang属性
    document.documentElement.setAttribute('lang', lang === 'zh' ? 'zh-CN' : 'en');
    document.documentElement.setAttribute('data-lang', lang);
    
    // 更新页面标题
    document.title = lang === 'zh' ? 'MacCrash 自动符号化工具' : 'MacCrash Auto Symbolizer';
    
    // 更新当前语言显示
    if (currentLangSpan) {
        currentLangSpan.textContent = languages[lang].name;
    }
    
    // 更新语言选项的active状态
    const langOptions = document.querySelectorAll('.lang-option');
    langOptions.forEach(option => {
        option.classList.toggle('active', option.dataset.lang === lang);
    });
    
    // 更新所有带有data-en和data-zh属性的元素
    updatePageText(lang);
    
    // 更新表单占位符
    updateFormPlaceholders(lang);
    
    // 强制更新输出框内容（如果是空的或占位内容）
    forceUpdateOutputBoxes(lang);
    
    // 关闭下拉菜单
    closeLangDropdown();
}

function updatePageText(lang) {
    const elements = document.querySelectorAll(`[data-${lang}]`);
    elements.forEach(element => {
        const text = element.getAttribute(`data-${lang}`);
        if (text) {
            // 对于某些特殊元素，需要特殊处理
            if (element.tagName === 'OPTION') {
                element.textContent = text;
            } else if (element.classList.contains('output-code')) {
                // 对于输出代码区域，简化检查逻辑
                const currentText = element.textContent.trim();
                const currentEmptyText = element.getAttribute(`data-empty-${lang}`);
                
                // 检查是否为空或占位内容
                const isEmptyOrPlaceholder = !currentText || 
                    isPlaceholderContent(currentText) ||
                    currentText === element.getAttribute(`data-empty-zh`) ||
                    currentText === element.getAttribute(`data-empty-en`);
                
                if (isEmptyOrPlaceholder && currentEmptyText) {
                    element.textContent = currentEmptyText;
                }
            } else {
                element.textContent = text;
            }
        }
    });
}

function updateFormPlaceholders(lang) {
    const elements = document.querySelectorAll(`[data-placeholder-${lang}]`);
    elements.forEach(element => {
        const placeholder = element.getAttribute(`data-placeholder-${lang}`);
        if (placeholder) {
            element.setAttribute('placeholder', placeholder);
        }
    });
}

// 表单验证
function initializeFormValidation() {
    const versionInput = document.getElementById('version');
    const archSelect = document.getElementById('arch');
    
    if (versionInput) {
        versionInput.addEventListener('input', function() {
            const version = this.value.trim();
            if (version && !isValidVersion(version)) {
                this.setCustomValidity(currentLang === 'zh' ? 
                    '请输入有效的版本号格式，例如: 45.8.0.32875' : 
                    'Please enter a valid version format, e.g., 45.8.0.32875');
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    // 表单验证
    if (symbolizeForm) {
        symbolizeForm.addEventListener('input', validateForm);
        symbolizeForm.addEventListener('change', validateForm);
    }
}

function isValidVersion(version) {
    const versionPattern = /^\d+\.\d+\.\d+\.\d+$/;
    return versionPattern.test(version);
}

function validateForm() {
    const version = document.getElementById('version')?.value.trim();
    const arch = document.getElementById('arch')?.value;
    const stackContent = document.getElementById('stack_content')?.value.trim();
    const hasFile = crashFile?.files.length > 0;
    
    let isValid = true;
    let errorMessage = '';
    
    if (!version) {
        isValid = false;
        errorMessage = currentLang === 'zh' ? '请输入版本号' : 'Please enter version number';
    } else if (!isValidVersion(version)) {
        isValid = false;
        errorMessage = currentLang === 'zh' ? '版本号格式不正确' : 'Invalid version format';
    } else if (!arch) {
        isValid = false;
        errorMessage = currentLang === 'zh' ? '请选择架构' : 'Please select architecture';
    } else if (currentActiveTab === 'text' && !stackContent) {
        isValid = false;
        errorMessage = currentLang === 'zh' ? '请输入Stack内容' : 'Please enter stack content';
    } else if (currentActiveTab === 'file' && !hasFile) {
        isValid = false;
        errorMessage = currentLang === 'zh' ? '请选择崩溃文件' : 'Please select crash file';
    }
    
    if (symbolizeBtn) {
        symbolizeBtn.disabled = !isValid || isProcessing;
        symbolizeBtn.title = errorMessage;
    }
}

// 切换输入方式
function switchInputMethod(method) {
    currentActiveTab = method;
    
    const textInput = document.getElementById('text-input');
    const fileInput = document.getElementById('file-input');
    
    if (method === 'text') {
        if (textInput) textInput.style.display = 'block';
        if (fileInput) fileInput.style.display = 'none';
        removeFile();
    } else {
        if (textInput) textInput.style.display = 'none';
        if (fileInput) fileInput.style.display = 'block';
        const stackContent = document.getElementById('stack_content');
        if (stackContent) stackContent.value = '';
    }
    
    validateForm();
}

// 切换输出选项卡
function switchOutputTab(tabName) {
    currentOutputTab = tabName;
    
    outputTabButtons.forEach(button => {
        button.classList.toggle('active', button.dataset.tab === tabName);
    });
    
    outputContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-output`);
    });
}

// 文件处理
function handleDragOver(e) {
    e.preventDefault();
    fileUploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    fileUploadArea.classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    fileUploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        crashFile.files = files;
        handleFileSelect();
    }
}

function handleFileSelect() {
    if (!crashFile || !crashFile.files) {
        console.error('File input element not available');
        return;
    }
    
    const file = crashFile.files[0];
    if (file) {
        if (fileName) {
            fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
        }
        
        if (fileInfo) {
            fileInfo.style.display = 'flex';
        }
        
        const uploadContent = fileUploadArea?.querySelector('.file-upload-content');
        if (uploadContent) {
            uploadContent.style.display = 'none';
        }
        
        validateForm();
    }
}

function removeFile() {
    if (crashFile) crashFile.value = '';
    if (fileInfo) fileInfo.style.display = 'none';
    const uploadContent = fileUploadArea?.querySelector('.file-upload-content');
    if (uploadContent) uploadContent.style.display = 'block';
    validateForm();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 表单提交处理
async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (isProcessing) return;
    
    isProcessing = true;
    updateSymbolizeButton(true);
    
    // 显示进度指示器
    if (progressIndicator) progressIndicator.style.display = 'block';
    
    // 自动切换到日志标签页以显示处理过程
    switchOutputTab('logs');
    
    // 清空之前的结果
    updateOutputAreas(
        currentLang === 'zh' ? '正在处理，请稍候...' : 'Processing, please wait...',
        currentLang === 'zh' ? '正在处理，请稍候...' : 'Processing, please wait...'
    );
    
    try {
        const formData = new FormData(symbolizeForm);
        
        // 根据当前输入方式处理表单数据
        if (currentActiveTab === 'text') {
            formData.delete('crash_file');
        } else {
            formData.delete('stack_content');
        }
        
        const response = await fetch('/symbolize', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            symbolizeResult.textContent = result.output || (
                currentLang === 'zh' ? '符号化完成，但没有输出内容。' : 'Symbolization completed, but no output content.'
            );
            showMessage(
                currentLang === 'zh' ? '符号化处理完成！' : 'Symbolization completed!',
                'success'
            );
        } else {
            symbolizeResult.textContent = `${currentLang === 'zh' ? '处理失败' : 'Processing failed'}:\n${result.error || (currentLang === 'zh' ? '未知错误' : 'Unknown error')}`;
            showMessage(
                `${currentLang === 'zh' ? '处理失败' : 'Processing failed'}: ${result.error || (currentLang === 'zh' ? '未知错误' : 'Unknown error')}`,
                'error'
            );
        }
        
        // 显示日志
        if (result.logs && result.logs.length > 0) {
            logsResult.textContent = result.logs.join('\n');
        } else {
            logsResult.textContent = currentLang === 'zh' ? '没有日志信息。' : 'No log information.';
        }
        
        // 处理完成后自动切换到结果标签页
        setTimeout(() => {
            switchOutputTab('result');
        }, 500); // 延迟500ms，让用户能看到日志更新
        
    } catch (error) {
        console.error('请求失败:', error);
        const errorMessage = `${currentLang === 'zh' ? '网络错误' : 'Network error'}: ${error.message}`;
        symbolizeResult.textContent = errorMessage;
        logsResult.textContent = errorMessage;
        showMessage(errorMessage, 'error');
        
        // 即使出错也切换到结果标签页显示错误信息
        setTimeout(() => {
            switchOutputTab('result');
        }, 500);
    } finally {
        isProcessing = false;
        updateSymbolizeButton(false);
        if (progressIndicator) progressIndicator.style.display = 'none';
        validateForm();
    }
}

function updateSymbolizeButton(processing) {
    if (!symbolizeBtn) return;
    
    if (processing) {
        symbolizeBtn.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            <span>${currentLang === 'zh' ? '处理中...' : 'Processing...'}</span>
        `;
        symbolizeBtn.disabled = true;
    } else {
        symbolizeBtn.innerHTML = `
            <i class="octicon octicon-play"></i>
            <span>${currentLang === 'zh' ? '开始符号化' : 'Start Symbolization'}</span>
        `;
        symbolizeBtn.disabled = false;
    }
}

function updateOutputAreas(resultText, logText) {
    if (symbolizeResult) symbolizeResult.textContent = resultText;
    if (logsResult) logsResult.textContent = logText;
}

// 清空结果
function clearResults() {
    const emptyResultText = currentLang === 'zh' ? 
        '等待开始符号化处理...\n点击"开始符号化"按钮来处理崩溃日志。' :
        'Waiting for symbolization to start...\nClick "Start Symbolization" to process crash logs.';
    const emptyLogText = currentLang === 'zh' ? '暂无日志信息...' : 'No log information available...';
    
    updateOutputAreas(emptyResultText, emptyLogText);
    showMessage(
        currentLang === 'zh' ? '结果已清空' : 'Results cleared',
        'info'
    );
}

// 复制结果
async function copyResult() {
    const activeOutput = currentOutputTab === 'result' ? symbolizeResult : logsResult;
    const text = activeOutput.textContent;
    
    try {
        await navigator.clipboard.writeText(text);
        showMessage(
            currentLang === 'zh' ? '已复制到剪贴板' : 'Copied to clipboard',
            'success'
        );
    } catch (error) {
        console.error('复制失败:', error);
        
        // 备用复制方法
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showMessage(
                currentLang === 'zh' ? '已复制到剪贴板' : 'Copied to clipboard',
                'success'
            );
        } catch (fallbackError) {
            showMessage(
                currentLang === 'zh' ? '复制失败，请手动复制' : 'Copy failed, please copy manually',
                'error'
            );
        }
        document.body.removeChild(textArea);
    }
}

// 下载结果
function downloadResult() {
    const activeOutput = currentOutputTab === 'result' ? symbolizeResult : logsResult;
    const text = activeOutput.textContent;
    const filename = currentOutputTab === 'result' ? 'symbolize_result.txt' : 'symbolize_logs.txt';
    
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showMessage(
        `${currentLang === 'zh' ? '文件已下载' : 'File downloaded'}: ${filename}`,
        'success'
    );
}

// 显示消息提示
function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flash-message ${type}`;
    
    const iconClass = {
        success: 'octicon octicon-check',
        error: 'octicon octicon-alert',
        info: 'octicon octicon-info'
    }[type] || 'octicon octicon-info';
    
    messageDiv.innerHTML = `
        <i class="${iconClass}"></i>
        <span>${message}</span>
    `;
    
    messageContainer.appendChild(messageDiv);
    
    // 3秒后自动移除消息
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 3000);
}

// 轮询日志更新（可选功能）
async function pollLogs() {
    if (!isProcessing) return;
    
    try {
        const response = await fetch('/logs');
        const result = await response.json();
        
        if (result.logs && result.logs.length > 0) {
            logsResult.textContent = result.logs.join('\n');
            // 自动滚动到底部
            logsResult.scrollTop = logsResult.scrollHeight;
        }
    } catch (error) {
        console.error('获取日志失败:', error);
    }
}

// 每秒轮询一次日志（当正在处理时）
setInterval(() => {
    if (isProcessing) {
        pollLogs();
    }
}, 1000);