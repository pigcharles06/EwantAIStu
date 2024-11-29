// 等待 DOM 加載完成
document.addEventListener('DOMContentLoaded', function() {
    // 每 100ms 檢查一次按鈕是否存在
    const interval = setInterval(function() {
        const submitButton = document.querySelector('button[type="submit"]');
        
        if (submitButton) {
            clearInterval(interval);
            
            // 創建連結容器
            const container = document.createElement('div');
            container.style.textAlign = 'center';
            container.style.marginTop = '16px';
            container.style.color = '#ffffff';
            
            // 添加註冊連結
            const registerLink = document.createElement('a');
            registerLink.href = '/public/register.html';
            registerLink.style.color = '#ff4772';
            registerLink.style.marginLeft = '5px';
            registerLink.style.textDecoration = 'none';
            registerLink.textContent = '點此註冊';
            registerLink.onclick = function(e) {
                e.preventDefault();
                window.location.href = window.location.origin + '/public/register.html';
            };
            
            container.appendChild(document.createTextNode('還沒有帳號？'));
            container.appendChild(registerLink);
            
            // 將容器插入到按鈕後面
            submitButton.parentNode.insertBefore(container, submitButton.nextSibling);
        }
    }, 100);
}); 