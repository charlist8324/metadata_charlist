let currentTableData = null;

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function parseDataType(dataType) {
    if (!dataType) {
        return { type: '-', length: '-' };
    }
    
    const match = dataType.match(/^(\w+)(?:\(([^)]+)\))?$/);
    if (match) {
        return {
            type: match[1],
            length: match[2] || '-'
        };
    }
    
    return { type: dataType, length: '-' };
}

async function loadTableDetails(tableId) {
    try {
        const response = await fetch(`/api/tables/${tableId}`);
        if (!response.ok) {
            if (response.status === 401) {
                alert('请先登录');
                window.location.href = '/login';
                return;
            }
            const errorData = await response.json().catch(() => ({ error: '未知错误' }));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const table = await response.json();
        currentTableData = table;
        
        // 更新页面标题
        document.getElementById('tableTitle').textContent = `表: ${table.table_name}`;
        document.title = `${table.table_name} - 表详情 - 元数据管理系统`;
        
        // 更新基本信息
        document.getElementById('detailTableName').textContent = table.table_name;
        document.getElementById('detailSchemaName').textContent = table.schema_name || '-';
        document.getElementById('detailRowCount').textContent = table.row_count?.toLocaleString() || '未知';
        document.getElementById('detailSizeBytes').textContent = formatBytes(table.size_bytes || 0);
        document.getElementById('detailComment').textContent = table.comment || '无';
        document.getElementById('detailCreatedAt').textContent = table.created_at ? new Date(table.created_at).toLocaleString() : '未知';
        document.getElementById('detailUpdatedAt').textContent = table.updated_at ? new Date(table.updated_at).toLocaleString() : '未知';
        
        // 加载字段信息
        loadColumns(table.columns);
        
    } catch (error) {
        console.error('加载表详情失败:', error);
        alert('加载表详情失败: ' + error.message);
    }
}

function loadColumns(columns) {
    const tbody = document.getElementById('columnsList');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!columns || columns.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-3 text-muted">暂无字段信息</td></tr>';
        return;
    }
    
    columns.forEach(column => {
        const parsedType = parseDataType(column.data_type);
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${column.column_name}</td>
            <td>${parsedType.type}</td>
            <td>${parsedType.length}</td>
            <td>${column.is_nullable === 'YES' ? '是' : '否'}</td>
            <td>${column.default_value || '-'}</td>
            <td>${column.ordinal_position || '-'}</td>
            <td>${column.column_comment || '-'}</td>
        `;
        tbody.appendChild(row);
    });
}

function checkAuthStatus() {
    fetch('/api/current-user')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('未登录');
        })
        .then(userData => {
            showUserMenu(userData);
        })
        .catch(error => {
            console.error('检查登录状态失败:', error);
            showLoginMenu();
        });
}

function showUserMenu(userData) {
    document.getElementById('usernameDisplay').textContent = userData.full_name || userData.username;
    document.getElementById('mainNavMenu').classList.remove('d-none');
    document.getElementById('userMenu').classList.remove('d-none');
    document.getElementById('loginMenu').classList.add('d-none');
}

function showLoginMenu() {
    document.getElementById('mainNavMenu').classList.remove('d-none');
    document.getElementById('userMenu').classList.add('d-none');
    document.getElementById('loginMenu').classList.remove('d-none');
}

async function logout() {
    if (!confirm('确定要退出登录吗？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            window.location.href = '/';
        } else {
            alert('退出登录失败');
        }
    } catch (error) {
        console.error('退出登录失败:', error);
        alert('退出登录失败');
    }
}

function showUserInfo() {
    alert('功能开发中：显示用户详细信息');
}