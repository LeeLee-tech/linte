// 全局变量
let schedules = [];
let editingId = null;
let currentFilterDate = null;
let currentScheduleId = null;
// 场所列表
let locations = ['酒吧', '商场', '饭店', '咖啡店', '公园', '电影院', '健身房', '图书馆', '办公室', '家', '学校', '医院', '银行', '超市', '药店', '加油站', '车站', '机场', '酒店', '餐厅', '咖啡馆', '茶馆', 'KTV', '夜总会', '游乐场', '博物馆', '美术馆', '体育馆', '游泳馆', '网球场', '篮球场', '足球场', '公园', '广场', '海滩', '山区', '湖泊', '河流', '森林', '购物中心', '百货公司', '便利店', '书店', '花店', '服装店', '电器店', '家具店', '建材市场', '汽车4S店', '修理厂', '洗车场', '停车场', '仓库', '工厂', '农场', '果园', '牧场', '温室', '实验室', '研究所', '会议室', '培训中心', '幼儿园', '小学', '中学', '大学', '职业学校', '培训机构', '驾校', '语言学校', '艺术学校', '音乐学校', '舞蹈学校', '武术学校', '瑜伽馆', '舞蹈室', '画室', '琴房', '录音棚', '摄影棚', '直播间', '工作室', '创意空间', '孵化园', '科技园', '创业园', '产业园', '工业园', '商业区', '工业区', '住宅区', '别墅区', '公寓', '宿舍', '民宿', '旅馆', '招待所', '度假村', '露营地', '房车营地', '主题公园', '水上乐园', '滑雪场', '高尔夫球场', '赛马场', '赛车场', '射击场', '射箭场', '攀岩馆', '蹦床馆', '桌游吧', '密室逃脱', '剧本杀', '轰趴馆', '棋牌室', '台球厅', '保龄球馆', '旱冰场', '溜冰场', '游泳馆', '冲浪馆', '潜水中心', '帆船俱乐部', '游艇码头', '钓鱼场', '狩猎场', '射击场', '靶场', '军事基地', '训练营', '拓展基地', '生存基地', '野营地', '徒步路线', '登山路线', '骑行路线', '跑步路线', '马拉松路线', '铁人三项路线', '赛车路线', '拉力赛路线', '自行车赛路线', '足球联赛场地', '篮球联赛场地', '排球联赛场地', '网球联赛场地', '乒乓球联赛场地', '羽毛球联赛场地', '棒球联赛场地', '橄榄球联赛场地', '曲棍球联赛场地', '手球联赛场地', '水球联赛场地', '冰球联赛场地', '滑雪比赛场地', '滑冰比赛场地', '游泳比赛场地', '跳水比赛场地', '体操比赛场地', '田径比赛场地', '举重比赛场地', '拳击比赛场地', '摔跤比赛场地', '柔道比赛场地', '跆拳道比赛场地', '武术比赛场地', '击剑比赛场地', '射击比赛场地', '射箭比赛场地', '马术比赛场地', '赛艇比赛场地', '皮划艇比赛场地', '帆船比赛场地', '冲浪比赛场地', '潜水比赛场地', '铁人三项比赛场地', '现代五项比赛场地', '冬季两项比赛场地', '雪橇比赛场地', '雪车比赛场地', '冰壶比赛场地', '短道速滑比赛场地', '速度滑冰比赛场地', '花样滑冰比赛场地', '冰球比赛场地', '滑雪比赛场地', '单板滑雪比赛场地', '自由式滑雪比赛场地', '北欧两项比赛场地', '跳台滑雪比赛场地', '越野滑雪比赛场地', '高山滑雪比赛场地', '超级大回转比赛场地', '大回转比赛场地', '回转比赛场地', '平行大回转比赛场地', '障碍追逐比赛场地', 'U型场地技巧比赛场地', '坡面障碍技巧比赛场地', '大跳台比赛场地', '空中技巧比赛场地', '雪上技巧比赛场地', '越野滑雪比赛场地', '冬季两项比赛场地', '雪橇比赛场地', '雪车比赛场地', '冰壶比赛场地'];
const API_BASE_URL = localStorage.getItem('api-base-url') || 'http://127.0.0.1:8000';
const AUTH_STORAGE_KEY = 'linte-auth-session';

// 加载待办内容
function loadTodoContent() {
    const todoData = localStorage.getItem('todo-data');
    if (todoData) {
        const { todos, completed } = JSON.parse(todoData);
        renderTodoList(todos, completed);
    } else {
        renderTodoList([], []);
    }
}

// 保存待办内容
function saveTodoContent(todos, completed) {
    const todoData = JSON.stringify({ todos, completed });
    localStorage.setItem('todo-data', todoData);
}

// 渲染待办列表
function renderTodoList(todos, completed) {
    const todoList = document.getElementById('todo-list');
    const completedList = document.getElementById('completed-list');
    
    // 清空现有列表
    todoList.innerHTML = '';
    completedList.innerHTML = '';
    
    // 渲染待办事项
    todos.forEach((todo, index) => {
        const todoItem = document.createElement('div');
        todoItem.style.display = 'flex';
        todoItem.style.alignItems = 'center';
        todoItem.style.marginBottom = '12px';
        todoItem.style.padding = '15px';
        todoItem.style.backgroundColor = 'var(--card-background)';
        todoItem.style.borderRadius = '12px';
        todoItem.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        todoItem.style.transition = 'all 0.3s ease';
        
        todoItem.innerHTML = `
            <div class="todo-checkbox" style="margin-right: 15px; cursor: pointer; font-size: 24px; color: var(--primary-color); width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 2px solid var(--primary-color); border-radius: 6px;">□</div>
            <div style="flex: 1; font-size: 16px; color: var(--text-color); font-weight: 500;">${todo}</div>
            <button class="delete-todo" style="margin-left: 10px; padding: 8px 12px; border: none; border-radius: 8px; background-color: #f44336; color: white; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.3s ease;">删除</button>
        `;
        
        // 添加悬停效果
        todoItem.addEventListener('mouseenter', function() {
            todoItem.style.transform = 'translateY(-2px)';
            todoItem.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        });
        
        todoItem.addEventListener('mouseleave', function() {
            todoItem.style.transform = 'translateY(0)';
            todoItem.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        });
        
        // 添加点击事件
        const checkbox = todoItem.querySelector('.todo-checkbox');
        checkbox.addEventListener('click', function() {
            const completedTodo = todos.splice(index, 1)[0];
            completed.push(completedTodo);
            saveTodoContent(todos, completed);
            renderTodoList(todos, completed);
        });
        
        // 添加删除事件
        const deleteBtn = todoItem.querySelector('.delete-todo');
        deleteBtn.addEventListener('click', function() {
            todos.splice(index, 1);
            saveTodoContent(todos, completed);
            renderTodoList(todos, completed);
        });
        
        todoList.appendChild(todoItem);
    });
    
    // 渲染已完成事项
    completed.forEach((todo, index) => {
        const completedItem = document.createElement('div');
        completedItem.style.display = 'flex';
        completedItem.style.alignItems = 'center';
        completedItem.style.marginBottom = '12px';
        completedItem.style.padding = '15px';
        completedItem.style.backgroundColor = 'var(--background-color)';
        completedItem.style.borderRadius = '12px';
        completedItem.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        completedItem.style.opacity = '0.8';
        completedItem.style.transition = 'all 0.3s ease';
        
        completedItem.innerHTML = `
            <div class="completed-checkbox" style="margin-right: 15px; cursor: pointer; font-size: 24px; color: var(--primary-color); width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 2px solid var(--primary-color); border-radius: 6px; background-color: var(--primary-color); color: white;">✔</div>
            <div style="flex: 1; font-size: 16px; color: var(--light-text); text-decoration: line-through; font-weight: 500;">${todo}</div>
            <button class="delete-completed" style="margin-left: 10px; padding: 8px 12px; border: none; border-radius: 8px; background-color: #f44336; color: white; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.3s ease;">删除</button>
        `;
        
        // 添加悬停效果
        completedItem.addEventListener('mouseenter', function() {
            completedItem.style.transform = 'translateY(-2px)';
            completedItem.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        });
        
        completedItem.addEventListener('mouseleave', function() {
            completedItem.style.transform = 'translateY(0)';
            completedItem.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        });
        
        // 添加点击事件
        const checkbox = completedItem.querySelector('.completed-checkbox');
        checkbox.addEventListener('click', function() {
            const todoItem = completed.splice(index, 1)[0];
            todos.unshift(todoItem);
            saveTodoContent(todos, completed);
            renderTodoList(todos, completed);
        });
        
        // 添加删除事件
        const deleteBtn = completedItem.querySelector('.delete-completed');
        deleteBtn.addEventListener('click', function() {
            completed.splice(index, 1);
            saveTodoContent(todos, completed);
            renderTodoList(todos, completed);
        });
        
        completedList.appendChild(completedItem);
    });
}

// 初始化
function init() {
    loadLocations();
    loadSchedules();
    updateDateDisplay();
    checkForPeriodicSummaries();
    renderSchedules();
    setupEventListeners();
    // 加载待办内容并显示
    loadTodoContent();
    document.getElementById('todo-modal').style.display = 'block';
}

// 从本地存储加载地点列表
function loadLocations() {
    const storedLocations = localStorage.getItem('locations');
    if (storedLocations) {
        locations = JSON.parse(storedLocations);
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 添加日程按钮
    document.getElementById('add-schedule-btn').addEventListener('click', function() {
        // 显示模态框
        document.getElementById('schedule-modal').style.display = 'block';
        // 设置模态框标题
        document.getElementById('modal-title').textContent = '添加日程';
        // 重置表单
        document.getElementById('schedule-form').reset();
        // 设置默认日期为当前筛选日期
        document.getElementById('date').value = currentFilterDate;
        // 重置编辑模式
        editingId = null;
    });

    // 模态框取消按钮
    document.getElementById('modal-cancel').addEventListener('click', function() {
        document.getElementById('schedule-modal').style.display = 'none';
        document.getElementById('schedule-form').reset();
        // 隐藏地点下拉列表
        document.getElementById('location-dropdown').style.display = 'none';
        // 重置编辑模式
        editingId = null;
    });

    // 地点输入框事件
    const locationInput = document.getElementById('location');
    const locationDropdown = document.getElementById('location-dropdown');

    locationInput.addEventListener('input', function() {
        const inputValue = this.value.toLowerCase();
        if (inputValue) {
            // 模糊匹配地点
            const matchedLocations = locations.filter(location => 
                location.toLowerCase().includes(inputValue)
            );
            
            if (matchedLocations.length > 0) {
                // 显示下拉列表
                locationDropdown.style.display = 'block';
                // 填充下拉列表
                locationDropdown.innerHTML = '';
                matchedLocations.forEach(location => {
                    const option = document.createElement('div');
                    option.style.padding = '8px';
                    option.style.cursor = 'pointer';
                    option.style.hover = 'background-color: #f5f5f5';
                    option.textContent = location;
                    option.addEventListener('click', function() {
                        locationInput.value = location;
                        locationDropdown.style.display = 'none';
                    });
                    option.addEventListener('mouseover', function() {
                        this.style.backgroundColor = '#f5f5f5';
                    });
                    option.addEventListener('mouseout', function() {
                        this.style.backgroundColor = 'white';
                    });
                    locationDropdown.appendChild(option);
                });
            } else {
                locationDropdown.style.display = 'none';
            }
        } else {
            locationDropdown.style.display = 'none';
        }
    });

    // 点击页面其他地方隐藏下拉列表
    document.addEventListener('click', function(e) {
        if (!locationInput.contains(e.target) && !locationDropdown.contains(e.target)) {
            locationDropdown.style.display = 'none';
        }
    });

    // 点击模态框空白处退出
    const modals = ['schedule-modal', 'schedule-detail-modal', 'delete-modal', 'summary-view-modal', 'summary-edit-modal', 'chat-modal', 'settings-modal', 'todo-modal', 'add-todo-modal'];
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    if (modalId === 'schedule-modal') {
                        document.getElementById('schedule-modal').style.display = 'none';
                        document.getElementById('schedule-form').reset();
                        document.getElementById('location-dropdown').style.display = 'none';
                        editingId = null;
                    } else if (modalId === 'schedule-detail-modal') {
                        hideDetailModal();
                    } else if (modalId === 'delete-modal') {
                        hideDeleteModal();
                    } else if (modalId === 'summary-view-modal') {
                        document.getElementById('summary-view-modal').style.display = 'none';
                    } else if (modalId === 'summary-edit-modal') {
                        document.getElementById('summary-edit-modal').style.display = 'none';
                    } else if (modalId === 'todo-modal') {
                        document.getElementById('todo-modal').style.display = 'none';
                    } else if (modalId === 'add-todo-modal') {
                        document.getElementById('add-todo-modal').style.display = 'none';
                    }
                }
            });
        }
    });

    // 表单提交
    document.getElementById('schedule-form').addEventListener('submit', function(e) {
        e.preventDefault();
        addSchedule();
    });

    // 日期输入框变化事件
    document.getElementById('date-display').addEventListener('change', function() {
        const selectedDate = this.value;
        if (selectedDate) {
            currentFilterDate = selectedDate;
            renderSchedules();
        }
    });







    // 查看总结按钮
    const viewSummaryBtn = document.getElementById('view-summary-btn');
    if (viewSummaryBtn) {
        viewSummaryBtn.addEventListener('click', function() {
            document.getElementById('summary-view-modal').style.display = 'block';
            loadSummaryTab('daily');
        });
    }

    // 编辑总结按钮
    const editSummaryBtn = document.getElementById('edit-summary-btn');
    if (editSummaryBtn) {
        editSummaryBtn.addEventListener('click', function() {
            document.getElementById('summary-edit-modal').style.display = 'block';
            loadEditSummaryTab('daily');
        });
    }

    // 关闭总结编辑界面
    const closeSummaryEditBtn = document.getElementById('close-summary-edit');
    if (closeSummaryEditBtn) {
        closeSummaryEditBtn.addEventListener('click', function() {
            document.getElementById('summary-edit-modal').style.display = 'none';
        });
    }

    // 关闭总结查看界面
    const closeSummaryViewBtn = document.getElementById('close-summary-view');
    if (closeSummaryViewBtn) {
        closeSummaryViewBtn.addEventListener('click', function() {
            document.getElementById('summary-view-modal').style.display = 'none';
        });
    }

    // 聊天按钮
    const chatBtn = document.getElementById('chat-btn');
    if (chatBtn) {
        chatBtn.addEventListener('click', function() {
            document.getElementById('main-page').style.display = 'none';
            document.getElementById('chat-page').style.display = 'block';
        });
    }

    // 返回主页面（从聊天页面）
    const backFromChatBtn = document.getElementById('back-from-chat');
    if (backFromChatBtn) {
        backFromChatBtn.addEventListener('click', function() {
            document.getElementById('chat-page').style.display = 'none';
            document.getElementById('main-page').style.display = 'block';
        });
    }

    // 设置按钮
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            document.getElementById('main-page').style.display = 'none';
            document.getElementById('settings-page').style.display = 'block';
        });
    }

    // 返回主页面（从设置页面）
    const backFromSettingsBtn = document.getElementById('back-from-settings');
    if (backFromSettingsBtn) {
        backFromSettingsBtn.addEventListener('click', function() {
            document.getElementById('settings-page').style.display = 'none';
            document.getElementById('main-page').style.display = 'block';
        });
    }

    // 待办按钮
    const todoBtn = document.getElementById('todo-btn');
    if (todoBtn) {
        todoBtn.addEventListener('click', function() {
            loadTodoContent();
            document.getElementById('todo-modal').style.display = 'block';
        });
    }

    // 关闭待办界面
    const closeTodoBtn = document.getElementById('close-todo');
    if (closeTodoBtn) {
        closeTodoBtn.addEventListener('click', function() {
            document.getElementById('todo-modal').style.display = 'none';
        });
    }

    // 添加待办事项按钮
    const addTodoBtn = document.getElementById('add-todo');
    if (addTodoBtn) {
        addTodoBtn.addEventListener('click', function() {
            document.getElementById('add-todo-modal').style.display = 'block';
        });
    }

    // 关闭添加待办事项界面
    const closeAddTodoBtn = document.getElementById('close-add-todo');
    if (closeAddTodoBtn) {
        closeAddTodoBtn.addEventListener('click', function() {
            document.getElementById('add-todo-modal').style.display = 'none';
        });
    }

    // 保存新待办事项
    const saveNewTodoBtn = document.getElementById('save-new-todo');
    if (saveNewTodoBtn) {
        saveNewTodoBtn.addEventListener('click', function() {
            const newTodo = document.getElementById('new-todo-input').value.trim();
            if (newTodo) {
                const todoData = localStorage.getItem('todo-data');
                let todos = [];
                let completed = [];
                if (todoData) {
                    const { todos: storedTodos, completed: storedCompleted } = JSON.parse(todoData);
                    todos = storedTodos;
                    completed = storedCompleted;
                }
                todos.unshift(newTodo);
                saveTodoContent(todos, completed);
                renderTodoList(todos, completed);
                document.getElementById('add-todo-modal').style.display = 'none';
                document.getElementById('new-todo-input').value = '';
            }
        });
    }

    // 总结标签页切换
    const summaryTabs = document.querySelectorAll('.summary-tab');
    summaryTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.id.replace('tab-', '');
            loadSummaryTab(tabId);
        });
    });

    // 删除确认模态框按钮
    const deleteConfirmBtn = document.getElementById('delete-confirm');
    const deleteCancelBtn = document.getElementById('delete-cancel');
    if (deleteConfirmBtn) {
        deleteConfirmBtn.addEventListener('click', function() {
            deleteSchedule();
        });
    }
    if (deleteCancelBtn) {
        deleteCancelBtn.addEventListener('click', function() {
            hideDeleteModal();
        });
    }

    // 日程详情模态框按钮
    const detailEditBtn = document.getElementById('detail-edit');
    const detailDeleteBtn = document.getElementById('detail-delete');
    const detailCloseBtn = document.getElementById('detail-close');
    if (detailEditBtn) {
        detailEditBtn.addEventListener('click', function() {
            if (currentScheduleId) {
                editSchedule(currentScheduleId);
                hideDetailModal();
            }
        });
    }
    if (detailDeleteBtn) {
        detailDeleteBtn.addEventListener('click', function() {
            if (currentScheduleId) {
                showDeleteModal(currentScheduleId);
                hideDetailModal();
            }
        });
    }
    if (detailCloseBtn) {
        detailCloseBtn.addEventListener('click', hideDetailModal);
    }
}

// 添加日程
function addSchedule() {
    const title = document.getElementById('title').value;
    const date = document.getElementById('date').value;
    const startTime = document.getElementById('start-time').value;
    const endTime = document.getElementById('end-time').value;
    const location = document.getElementById('location').value;

    // 地点匹配逻辑
    if (!locations.includes(location)) {
        // 如果地点不在列表中，添加到列表
        locations.push(location);
        // 保存地点列表到本地存储
        localStorage.setItem('locations', JSON.stringify(locations));
    }

    if (editingId) {
        // 编辑现有日程
        const index = schedules.findIndex(schedule => schedule.id === editingId);
        if (index !== -1) {
            schedules[index] = {
                ...schedules[index],
                title,
                date,
                startTime,
                endTime,
                location
            };
        }
        editingId = null;
    } else {
        // 添加新日程
        const newSchedule = {
            id: Date.now().toString(),
            title,
            date,
            startTime,
            endTime,
            location
        };
        schedules.push(newSchedule);
    }

    saveSchedules();
    renderSchedules();
    document.getElementById('schedule-modal').style.display = 'none';
    document.getElementById('schedule-form').reset();
    // 隐藏地点下拉列表
    document.getElementById('location-dropdown').style.display = 'none';
    // 重置编辑模式
    editingId = null;
}

// 更新日期显示
function updateDateDisplay() {
    // 如果currentFilterDate已设置，则使用它，否则使用今天的日期
    let dateString;
    if (currentFilterDate) {
        dateString = currentFilterDate;
    } else {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        dateString = `${year}-${month}-${day}`;
        currentFilterDate = dateString;
    }
    document.getElementById('date-display').value = dateString;
    // 设置默认添加日程的日期为当前筛选日期
    document.getElementById('date').value = dateString;
}

// 从本地存储加载日程
function loadSchedules() {
    const storedSchedules = localStorage.getItem('schedules');
    if (storedSchedules) {
        schedules = JSON.parse(storedSchedules);
    }
}

// 保存日程到本地存储
function saveSchedules() {
    localStorage.setItem('schedules', JSON.stringify(schedules));
}

// 删除日程
function deleteSchedule(id) {
    // 如果没有传递id，从模态框获取
    if (!id) {
        const deleteModal = document.getElementById('delete-modal');
        id = deleteModal.dataset.scheduleId;
    }
    if (id) {
        schedules = schedules.filter(schedule => schedule.id !== id);
        saveSchedules();
        renderSchedules();
        hideDeleteModal();
    }
}

// 编辑日程
function editSchedule(id) {
    const schedule = schedules.find(schedule => schedule.id === id);
    if (schedule) {
        // 显示模态框
        document.getElementById('schedule-modal').style.display = 'block';
        // 设置模态框标题
        document.getElementById('modal-title').textContent = '编辑日程';
        // 预填表单字段
        document.getElementById('title').value = schedule.title;
        document.getElementById('date').value = schedule.date;
        document.getElementById('start-time').value = schedule.startTime;
        document.getElementById('end-time').value = schedule.endTime;
        document.getElementById('location').value = schedule.location;
        // 设置编辑模式
        editingId = id;
    }
}

// 显示删除确认模态框
function showDeleteModal(id) {
    const deleteModal = document.getElementById('delete-modal');
    deleteModal.style.display = 'block';
    // 存储当前日程ID
    deleteModal.dataset.scheduleId = id;
}

// 隐藏删除确认模态框
function hideDeleteModal() {
    document.getElementById('delete-modal').style.display = 'none';
}

// 显示日程详情模态框
function showDetailModal(id) {
    const schedule = schedules.find(schedule => schedule.id === id);
    if (schedule) {
        // 填充详情
        document.getElementById('detail-schedule-title').textContent = schedule.title;
        document.getElementById('detail-schedule-date').textContent = schedule.date;
        document.getElementById('detail-schedule-time').textContent = `${schedule.startTime} - ${schedule.endTime}`;
        document.getElementById('detail-schedule-location').textContent = schedule.location || '未设置';
        
        // 存储当前日程ID
        currentScheduleId = id;
        
        // 显示模态框
        document.getElementById('schedule-detail-modal').style.display = 'block';
    }
}

// 隐藏日程详情模态框
function hideDetailModal() {
    document.getElementById('schedule-detail-modal').style.display = 'none';
    currentScheduleId = null;
}

// 渲染日程列表
function renderSchedules() {
    const scheduleGridMorning = document.getElementById('schedule-grid-morning');
    const scheduleGridAfternoon = document.getElementById('schedule-grid-afternoon');
    
    // 清空现有的日程项
    const existingItemsMorning = scheduleGridMorning.querySelectorAll('.schedule-item');
    existingItemsMorning.forEach(item => item.remove());
    
    const existingItemsAfternoon = scheduleGridAfternoon.querySelectorAll('.schedule-item');
    existingItemsAfternoon.forEach(item => item.remove());

    // 筛选出当前日期的日程
    const filteredSchedules = schedules.filter(schedule => schedule.date === currentFilterDate && schedule.startTime && schedule.endTime);

    // 按时间排序
    const sortedSchedules = [...filteredSchedules].sort((a, b) => {
        return a.startTime.localeCompare(b.startTime);
    });

    // 颜色数组，用于为不同的日程分配不同的颜色
    const colors = ['#4CAF50', '#2196F3', '#ff9800', '#9c27b0', '#f44336', '#3f51b5', '#00bcd4', '#8bc34a', '#ff5722', '#673ab7'];

    // 添加日程项
    sortedSchedules.forEach((schedule, index) => {
        // 为每个日程分配一个颜色
        const colorIndex = index % colors.length;
        const color = colors[colorIndex];
        
        // 计算开始时间的位置
        const startTimeParts = schedule.startTime.split(':');
        const startHours = parseInt(startTimeParts[0]);
        const startMinutes = parseInt(startTimeParts[1]);
        const startTotalMinutes = startHours * 60 + startMinutes;
        
        // 计算结束时间和高度
        const endTimeParts = schedule.endTime.split(':');
        const endHours = parseInt(endTimeParts[0]);
        const endMinutes = parseInt(endTimeParts[1]);
        const endTotalMinutes = endHours * 60 + endMinutes;
        
        // 检查日程是否跨越12点
        const crossesNoon = startTotalMinutes < 12 * 60 && endTotalMinutes > 12 * 60;
        
        if (crossesNoon) {
            // 跨越12点的日程，分为两部分显示
            
            // 上午部分：从开始时间到12:00
            const morningDurationMinutes = 12 * 60 - startTotalMinutes;
            const morningHeight = (morningDurationMinutes / 60) * 120;
            const morningTop = 60 + (startTotalMinutes / 60) * 120;
            
            const morningItem = document.createElement('div');
            morningItem.className = 'schedule-item';
            morningItem.style.backgroundColor = color;
            morningItem.style.top = `${morningTop}px`;
            morningItem.style.height = `${morningHeight}px`;
            morningItem.style.width = '95%';
            morningItem.style.left = '2.5%';
            
            morningItem.innerHTML = `
                <div class="title">${schedule.title}</div>
                <div class="time">${schedule.startTime} - 12:00</div>
                ${schedule.location ? `<div class="description">地点: ${schedule.location}</div>` : ''}
            `;
            
            // 添加点击事件来打开详情模态框
            (function(id) {
                morningItem.addEventListener('click', function() {
                    showDetailModal(id);
                });
            })(schedule.id);
            
            scheduleGridMorning.appendChild(morningItem);
            
            // 下午部分：从12:00到结束时间
            const afternoonDurationMinutes = endTotalMinutes - 12 * 60;
            const afternoonHeight = (afternoonDurationMinutes / 60) * 120;
            const afternoonTop = 60; // 从12点开始，顶部空白行下方
            
            const afternoonItem = document.createElement('div');
            afternoonItem.className = 'schedule-item';
            afternoonItem.style.backgroundColor = color;
            afternoonItem.style.top = `${afternoonTop}px`;
            afternoonItem.style.height = `${afternoonHeight}px`;
            afternoonItem.style.width = '95%';
            afternoonItem.style.left = '2.5%';
            
            afternoonItem.innerHTML = `
                <div class="title">${schedule.title}</div>
                <div class="time">12:00 - ${schedule.endTime}</div>
                ${schedule.location ? `<div class="description">地点: ${schedule.location}</div>` : ''}
            `;
            
            // 添加点击事件来打开详情模态框
            (function(id) {
                afternoonItem.addEventListener('click', function() {
                    showDetailModal(id);
                });
            })(schedule.id);
            
            scheduleGridAfternoon.appendChild(afternoonItem);
        } else if (startHours < 13) {
            // 上午日程，且不跨越12点
            const durationMinutes = endTotalMinutes - startTotalMinutes;
            const height = (durationMinutes / 60) * 120;
            const top = 60 + (startTotalMinutes / 60) * 120;
            
            const scheduleItem = document.createElement('div');
            scheduleItem.className = 'schedule-item';
            scheduleItem.style.backgroundColor = color;
            scheduleItem.style.top = `${top}px`;
            scheduleItem.style.height = `${height}px`;
            scheduleItem.style.width = '95%';
            scheduleItem.style.left = '2.5%';
            
            scheduleItem.innerHTML = `
                <div class="title">${schedule.title}</div>
                <div class="time">${schedule.startTime} - ${schedule.endTime}</div>
                ${schedule.location ? `<div class="description">地点: ${schedule.location}</div>` : ''}
            `;
            
            // 添加点击事件来打开详情模态框
            (function(id) {
                scheduleItem.addEventListener('click', function() {
                    showDetailModal(id);
                });
            })(schedule.id);
            
            scheduleGridMorning.appendChild(scheduleItem);
        } else {
            // 下午日程
            const durationMinutes = endTotalMinutes - startTotalMinutes;
            const height = (durationMinutes / 60) * 120;
            const top = 60 + ((startTotalMinutes - 12 * 60) / 60) * 120;
            
            const scheduleItem = document.createElement('div');
            scheduleItem.className = 'schedule-item';
            scheduleItem.style.backgroundColor = color;
            scheduleItem.style.top = `${top}px`;
            scheduleItem.style.height = `${height}px`;
            scheduleItem.style.width = '95%';
            scheduleItem.style.left = '2.5%';
            
            scheduleItem.innerHTML = `
                <div class="title">${schedule.title}</div>
                <div class="time">${schedule.startTime} - ${schedule.endTime}</div>
                ${schedule.location ? `<div class="description">地点: ${schedule.location}</div>` : ''}
            `;
            
            // 添加点击事件来打开详情模态框
            (function(id) {
                scheduleItem.addEventListener('click', function() {
                    showDetailModal(id);
                });
            })(schedule.id);
            
            scheduleGridAfternoon.appendChild(scheduleItem);
        }
    });
}

// 加载每日总结
function loadDailySummary() {
    const summary = localStorage.getItem(`daily-summary-${currentFilterDate}`);
    if (summary) {
        document.getElementById('daily-summary').value = summary;
    } else {
        document.getElementById('daily-summary').value = '';
    }
}

// 检查并显示特殊日期的总结框
function checkAndDisplaySpecialDateSummaries() {
    const container = document.getElementById('special-date-summaries');
    container.innerHTML = '';
    
    const selectedDate = new Date(currentFilterDate);
    const dayOfWeek = selectedDate.getDay(); // 0 是周日
    const dayOfMonth = selectedDate.getDate();
    const month = selectedDate.getMonth();
    const year = selectedDate.getFullYear();
    
    // 检查是否是周日
    if (dayOfWeek === 0) {
        const weekStart = new Date(selectedDate);
        // 调整到本周的开始（星期一）
        const daysToMonday = 6; // 周日距离周一有6天
        weekStart.setDate(selectedDate.getDate() - daysToMonday);
        const weekKey = `week-summary-${year}-${String(weekStart.getMonth() + 1).padStart(2, '0')}-${String(weekStart.getDate()).padStart(2, '0')}`;
        const existingSummary = localStorage.getItem(weekKey);
        
        // 添加周总结框
        const weekSummaryDiv = document.createElement('div');
        weekSummaryDiv.style.marginBottom = '20px';
        weekSummaryDiv.style.padding = '15px';
        weekSummaryDiv.style.border = '1px solid #ddd';
        weekSummaryDiv.style.borderRadius = '8px';
        weekSummaryDiv.style.backgroundColor = '#e3f2fd';
        
        weekSummaryDiv.innerHTML = `
            <h3 style="margin-bottom: 10px; color: #1976d2;">一周总结</h3>
            <textarea id="week-summary" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;">${existingSummary || ''}</textarea>
            <div style="text-align: right; margin-top: 10px;">
                <button onclick="saveWeekSummary('${weekKey}')" style="padding: 8px 16px; border: none; border-radius: 4px; background-color: #2196F3; color: white; cursor: pointer; transition: all 0.3s ease;">保存周总结</button>
            </div>
        `;
        
        container.appendChild(weekSummaryDiv);
    }
    
    // 检查是否是月末
    const nextDay = new Date(selectedDate);
    nextDay.setDate(dayOfMonth + 1);
    if (nextDay.getMonth() !== month) {
        const monthKey = `month-summary-${year}-${month + 1}`;
        const existingSummary = localStorage.getItem(monthKey);
        
        // 添加月度总结框
        const monthSummaryDiv = document.createElement('div');
        monthSummaryDiv.style.marginBottom = '20px';
        monthSummaryDiv.style.padding = '15px';
        monthSummaryDiv.style.border = '1px solid #ddd';
        monthSummaryDiv.style.borderRadius = '8px';
        monthSummaryDiv.style.backgroundColor = '#fff3e0';
        
        monthSummaryDiv.innerHTML = `
            <h3 style="margin-bottom: 10px; color: #f57c00;">月度总结</h3>
            <textarea id="month-summary" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;">${existingSummary || ''}</textarea>
            <div style="text-align: right; margin-top: 10px;">
                <button onclick="saveMonthSummary('${monthKey}')" style="padding: 8px 16px; border: none; border-radius: 4px; background-color: #ff9800; color: white; cursor: pointer; transition: all 0.3s ease;">保存月度总结</button>
            </div>
        `;
        
        container.appendChild(monthSummaryDiv);
    }
    
    // 检查是否是年末
    if (month === 11 && dayOfMonth === 31) {
        const yearKey = `year-summary-${year}`;
        const existingSummary = localStorage.getItem(yearKey);
        
        // 添加年度总结框
        const yearSummaryDiv = document.createElement('div');
        yearSummaryDiv.style.marginBottom = '20px';
        yearSummaryDiv.style.padding = '15px';
        yearSummaryDiv.style.border = '1px solid #ddd';
        yearSummaryDiv.style.borderRadius = '8px';
        yearSummaryDiv.style.backgroundColor = '#f3e5f5';
        
        yearSummaryDiv.innerHTML = `
            <h3 style="margin-bottom: 10px; color: #7b1fa2;">年度总结</h3>
            <textarea id="year-summary" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;">${existingSummary || ''}</textarea>
            <div style="text-align: right; margin-top: 10px;">
                <button onclick="saveYearSummary('${yearKey}')" style="padding: 8px 16px; border: none; border-radius: 4px; background-color: #9c27b0; color: white; cursor: pointer; transition: all 0.3s ease;">保存年度总结</button>
            </div>
        `;
        
        container.appendChild(yearSummaryDiv);
    }
}

// 保存每日总结
function saveDailySummary() {
    const summary = document.getElementById('daily-summary').value;
    localStorage.setItem(`daily-summary-${currentFilterDate}`, summary);
    alert('总结已保存');
}

// 保存周总结
function saveWeekSummary(key) {
    const summary = document.getElementById('week-summary').value;
    localStorage.setItem(key, summary);
    alert('周总结已保存');
}

// 保存月度总结
function saveMonthSummary(key) {
    const summary = document.getElementById('month-summary').value;
    localStorage.setItem(key, summary);
    alert('月度总结已保存');
}

// 保存年度总结
function saveYearSummary(key) {
    const summary = document.getElementById('year-summary').value;
    localStorage.setItem(key, summary);
    alert('年度总结已保存');
}

// 检查是否需要定期总结
function checkForPeriodicSummaries() {
    const today = new Date();
    const dayOfWeek = today.getDay(); // 0 是周日
    const dayOfMonth = today.getDate();
    const month = today.getMonth();
    const year = today.getFullYear();
    
    // 检查是否是周日
    if (dayOfWeek === 0) {
        const weekStart = new Date(today);
        // 调整到本周的开始（星期一）
        const daysToMonday = 6; // 周日距离周一有6天
        weekStart.setDate(today.getDate() - daysToMonday);
        const weekKey = `week-summary-${year}-${String(weekStart.getMonth() + 1).padStart(2, '0')}-${String(weekStart.getDate()).padStart(2, '0')}`;
        if (!localStorage.getItem(weekKey)) {
            if (confirm('今天是周日，是否添加本周总结？')) {
                addPeriodicSummary('周总结', weekKey);
            }
        }
    }
    
    // 检查是否是月末
    const nextDay = new Date(today);
    nextDay.setDate(dayOfMonth + 1);
    if (nextDay.getMonth() !== month) {
        const monthKey = `month-summary-${year}-${month + 1}`;
        if (!localStorage.getItem(monthKey)) {
            if (confirm('今天是月末，是否添加本月总结？')) {
                addPeriodicSummary('月度总结', monthKey);
            }
        }
    }
    
    // 检查是否是年末
    if (month === 11 && dayOfMonth === 31) {
        const yearKey = `year-summary-${year}`;
        if (!localStorage.getItem(yearKey)) {
            if (confirm('今天是年末，是否添加本年总结？')) {
                addPeriodicSummary('年度总结', yearKey);
            }
        }
    }
}

// 添加定期总结
function addPeriodicSummary(title, key) {
    const summary = prompt(`请输入${title}：`);
    if (summary) {
        localStorage.setItem(key, summary);
        alert(`${title}已保存`);
    }
}



// 编辑定期总结
function editPeriodicSummary(title, key) {
    const currentSummary = localStorage.getItem(key);
    const newSummary = prompt(`请编辑${title}：`, currentSummary);
    if (newSummary !== null) {
        localStorage.setItem(key, newSummary);
        alert(`${title}已更新`);
        
        // 根据总结类型重新显示列表
        if (key.startsWith('week-summary-')) {
            viewWeeklySummaries();
            // 如果当前在总结查看界面，也更新显示
            if (document.getElementById('summary-view-modal').style.display === 'block') {
                loadSummaryTab('weekly');
            }
        } else if (key.startsWith('month-summary-')) {
            viewMonthlySummaries();
            if (document.getElementById('summary-view-modal').style.display === 'block') {
                loadSummaryTab('monthly');
            }
        } else if (key.startsWith('year-summary-')) {
            viewYearlySummaries();
            if (document.getElementById('summary-view-modal').style.display === 'block') {
                loadSummaryTab('yearly');
            }
        } else if (key.startsWith('daily-summary-')) {
            if (document.getElementById('summary-view-modal').style.display === 'block') {
                loadSummaryTab('daily');
            }
        }
    }
}

// 删除定期总结
function deletePeriodicSummary(key) {
    if (confirm('确定要删除这个总结吗？')) {
        localStorage.removeItem(key);
        alert('总结已删除');
        
        // 根据总结类型重新显示列表
        if (key.startsWith('week-summary-')) {
            viewWeeklySummaries();
            // 如果当前在总结查看界面，也更新显示
            if (document.getElementById('summary-view-modal').style.display === 'block') {
                loadSummaryTab('weekly');
            }
        } else if (key.startsWith('month-summary-')) {
            viewMonthlySummaries();
            if (document.getElementById('summary-view-modal').style.display === 'block') {
                loadSummaryTab('monthly');
            }
        } else if (key.startsWith('year-summary-')) {
            viewYearlySummaries();
            if (document.getElementById('summary-view-modal').style.display === 'block') {
                loadSummaryTab('yearly');
            }
        } else if (key.startsWith('daily-summary-')) {
            if (document.getElementById('summary-view-modal').style.display === 'block') {
                loadSummaryTab('daily');
            }
        }
    }
}

// 计算一年中的第几周
function getWeekNumber(date) {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear = (date - firstDayOfYear) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
}

// 生成过去12个月的月份列表
function getPastMonths() {
    const months = [];
    const today = new Date();
    for (let i = 0; i < 12; i++) {
        const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
        const yearMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        months.push(yearMonth);
    }
    return months;
}

// 生成过去52周和未来4周的周列表
function getPastWeeks() {
    const weeks = [];
    const today = new Date();
    // 生成过去52周和未来4周，总共56周
    for (let i = -4; i < 52; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() - i * 7);
        // 调整到本周的开始（星期一）
        const dayOfWeek = date.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        date.setDate(date.getDate() - daysToMonday);
        const weekStart = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
        weeks.push(weekStart);
    }
    return weeks;
}

// 生成过去5年的年份列表
function getPastYears() {
    const years = [];
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 5; i++) {
        years.push((currentYear - i).toString());
    }
    return years;
}

// 计算月份的周数
function getMonthWeekNumber(date) {
    const month = date.getMonth();
    const weekStart = new Date(date);
    // 调整到本周的开始（星期一）
    const dayOfWeek = date.getDay();
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    weekStart.setDate(date.getDate() - daysToMonday);
    
    // 检查这一周是否有日子属于上个月
    for (let i = 0; i < 7; i++) {
        const currentDay = new Date(weekStart);
        currentDay.setDate(weekStart.getDate() + i);
        if (currentDay.getMonth() === month - 1) {
            // 有日子属于上个月，不计算为当月的周
            return 0;
        }
    }
    
    // 计算从月份开始到周开始的天数
    const monthStart = new Date(date.getFullYear(), month, 1);
    const diffDays = Math.floor((weekStart - monthStart) / (1000 * 60 * 60 * 24));
    const weekNumber = Math.floor(diffDays / 7) + 1;
    return weekNumber;
}

// 加载总结标签页
function loadSummaryTab(tabType) {
    const contentDiv = document.getElementById('summary-content');
    let content = '';
    
    switch (tabType) {
        case 'daily':
            content = '<h4>每日总结</h4>';
            // 获取过去12个月
            const months = getPastMonths();
            
            months.forEach(month => {
                content += `<div style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: white;">
                    <h5 style="margin-bottom: 10px;">${month}</h5>
                    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px;">
                `;
                
                // 生成日历网格
                const monthStart = new Date(month + '-01');
                const startDate = new Date(monthStart);
                startDate.setDate(startDate.getDate() - startDate.getDay());
                
                for (let i = 0; i < 42; i++) { // 6周 * 7天
                    const currentDate = new Date(startDate);
                    currentDate.setDate(startDate.getDate() + i);
                    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(currentDate.getDate()).padStart(2, '0')}`;
                    const key = `daily-summary-${dateStr}`;
                    const summary = localStorage.getItem(key);
                    
                    content += `<div onclick="openDailySummary('${key}')" style="padding: 10px; border: 1px solid #ddd; border-radius: 4px; min-height: 80px; cursor: pointer; ${currentDate.getMonth() !== monthStart.getMonth() ? 'background-color: #f5f5f5;' : summary ? 'background-color: #e8f5e8;' : ''} transition: background-color 0.3s ease; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px; text-align: center;">${currentDate.getDate()}</div>
                        ${summary ? '<div style="font-size: 12px; color: #4CAF50; text-align: center;">有总结</div>' : ''}
                    </div>`;
                }
                
                content += `</div></div>`;
            });
            break;
        
        case 'weekly':
            content = '<h4>周总结</h4>';
            // 获取过去52周
            const weeks = getPastWeeks();
            
            // 按月份分组
            const weeksByMonth = {};
            weeks.forEach(weekStartStr => {
                const weekStart = new Date(weekStartStr);
                const monthKey = `${weekStart.getFullYear()}-${String(weekStart.getMonth() + 1).padStart(2, '0')}`;
                if (!weeksByMonth[monthKey]) {
                    weeksByMonth[monthKey] = [];
                }
                weeksByMonth[monthKey].push(weekStartStr);
            });
            
            // 按月份排序
            const sortedMonthKeys = Object.keys(weeksByMonth).sort((a, b) => b.localeCompare(a));
            
            sortedMonthKeys.forEach(monthKey => {
                const [year, month] = monthKey.split('-');
                content += `<div style="margin-bottom: 20px;">
                    <h5 style="margin-bottom: 10px;">${year}年${month}月</h5>
                `;
                
                const monthWeeks = weeksByMonth[monthKey];
                monthWeeks.forEach(weekStartStr => {
                    const weekStart = new Date(weekStartStr);
                    // 使用周开始日期计算周数，确保横跨月份的周被正确计算
                    const weekNumber = getMonthWeekNumber(weekStart);
                    
                    // 只显示周数大于0的周
                    if (weekNumber > 0) {
                        const key = `week-summary-${weekStartStr}`;
                        const summary = localStorage.getItem(key);
                        
                        content += `<div onclick="viewSummaryDetail('周总结', '${key}', '${year}年${month}月第${weekNumber}周')" style="margin-bottom: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; ${summary ? 'background-color: #e3f2fd;' : 'background-color: white;'} transition: background-color 0.3s ease;">
                                <strong style="font-size: 16px;">第${weekNumber}周</strong>
                                ${summary ? '<div style="margin-top: 5px; font-size: 14px; color: #2196F3;">有总结</div>' : ''}
                            </div>`;
                    }
                });
                
                content += `</div>`;
            });
            break;
        
        case 'monthly':
            content = '<h4>月度总结</h4>';
            // 获取过去12个月
            const monthsList = getPastMonths();
            
            // 按年份分组
            const monthsByYear = {};
            monthsList.forEach(month => {
                const [year, monthNum] = month.split('-');
                if (!monthsByYear[year]) {
                    monthsByYear[year] = [];
                }
                monthsByYear[year].push(month);
            });
            
            // 按年份排序
            const sortedYearKeys = Object.keys(monthsByYear).sort((a, b) => b.localeCompare(a));
            
            sortedYearKeys.forEach(year => {
                content += `<div style="margin-bottom: 20px;">
                    <h5 style="margin-bottom: 10px;">${year}年</h5>
                `;
                
                const yearMonths = monthsByYear[year];
                yearMonths.forEach(month => {
                    const [, monthNum] = month.split('-');
                    const key = `month-summary-${month}`;
                    const summary = localStorage.getItem(key);
                    
                    content += `<div onclick="viewSummaryDetail('月度总结', '${key}', '${year}年${monthNum}月')" style="margin-bottom: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; ${summary ? 'background-color: #fff3e0;' : 'background-color: white;'} transition: background-color 0.3s ease;">
                        <strong style="font-size: 16px;">${monthNum}月</strong>
                        ${summary ? '<div style="margin-top: 5px; font-size: 14px; color: #ff9800;">有总结</div>' : ''}
                    </div>`;
                });
                
                content += `</div>`;
            });
            break;
        
        case 'yearly':
            content = '<h4>年度总结</h4>';
            // 获取过去5年
            const years = getPastYears();
            
            years.forEach(year => {
                const key = `year-summary-${year}`;
                const summary = localStorage.getItem(key);
                
                content += `<div onclick="viewSummaryDetail('年度总结', '${key}', '${year}年')" style="margin-bottom: 15px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; ${summary ? 'background-color: #f3e5f5;' : 'background-color: white;'} transition: background-color 0.3s ease;">
                    <strong style="font-size: 16px;">${year}年</strong>
                    ${summary ? '<div style="margin-top: 5px; font-size: 14px; color: #9c27b0;">有总结</div>' : ''}
                </div>`;
            });
            break;
    }
    
    contentDiv.innerHTML = content;
}

// 打开每日总结详情
function openDailySummary(key) {
    const summary = localStorage.getItem(key);
    const date = key.replace('daily-summary-', '');
    
    alert(`日期：${date}\n\n总结：${summary || '无'}`);
}

// 查看总结详情
function viewSummaryDetail(title, key, displayTitle) {
    const summary = localStorage.getItem(key);
    alert(`${displayTitle}\n\n${title}：${summary || '无'}`);
}

// 加载总结编辑标签页
function loadEditSummaryTab(tabType) {
    const contentDiv = document.getElementById('summary-edit-content');
    let content = '';
    
    // 使用当前主界面显示的日期
    const currentDate = currentFilterDate;
    const selectedDate = new Date(currentDate);
    const dayOfWeek = selectedDate.getDay(); // 0 是周日
    const dayOfMonth = selectedDate.getDate();
    const month = selectedDate.getMonth();
    const year = selectedDate.getFullYear();
    
    // 检查是否是月末
    const nextDay = new Date(selectedDate);
    nextDay.setDate(dayOfMonth + 1);
    const isMonthEnd = nextDay.getMonth() !== month;
    
    // 检查是否是年末
    const isYearEnd = (month === 11 && dayOfMonth === 31);
    
    // 始终显示每日总结
    content += `
        <div style="margin-bottom: 20px;">
            <h4 style="margin-bottom: 10px; color: #4CAF50;">每日总结</h4>
            <textarea id="edit-daily-summary" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;"></textarea>
            <div style="text-align: right; margin-top: 10px;">
                <button onclick="saveEditedDailySummary()" style="padding: 8px 16px; border: none; border-radius: 4px; background-color: #4CAF50; color: white; cursor: pointer; transition: all 0.3s ease;">保存</button>
            </div>
        </div>
    `;
    
    // 到了周末才显示周总结的编辑
    if (dayOfWeek === 0) {
        content += `
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px; color: #2196F3;">周总结</h4>
                <textarea id="edit-week-summary" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;"></textarea>
                <div style="text-align: right; margin-top: 10px;">
                    <button onclick="saveEditedWeekSummary()" style="padding: 8px 16px; border: none; border-radius: 4px; background-color: #2196F3; color: white; cursor: pointer; transition: all 0.3s ease;">保存</button>
                </div>
            </div>
        `;
    }
    
    // 到了月末才显示月总结的编辑
    if (isMonthEnd) {
        content += `
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px; color: #ff9800;">月度总结</h4>
                <textarea id="edit-month-summary" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;"></textarea>
                <div style="text-align: right; margin-top: 10px;">
                    <button onclick="saveEditedMonthSummary()" style="padding: 8px 16px; border: none; border-radius: 4px; background-color: #ff9800; color: white; cursor: pointer; transition: all 0.3s ease;">保存</button>
                </div>
            </div>
        `;
    }
    
    // 到了年末才显示年度总结的编辑
    if (isYearEnd) {
        content += `
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 10px; color: #9c27b0;">年度总结</h4>
                <textarea id="edit-year-summary" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;"></textarea>
                <div style="text-align: right; margin-top: 10px;">
                    <button onclick="saveEditedYearSummary()" style="padding: 8px 16px; border: none; border-radius: 4px; background-color: #9c27b0; color: white; cursor: pointer; transition: all 0.3s ease;">保存</button>
                </div>
            </div>
        `;
    }
    
    contentDiv.innerHTML = content;
    
    // 加载当前日期的总结内容
    loadCurrentDateSummaries();
}

// 加载当前日期的总结内容
function loadCurrentDateSummaries() {
    // 加载每日总结
    const dailySummary = localStorage.getItem(`daily-summary-${currentFilterDate}`);
    if (dailySummary) {
        document.getElementById('edit-daily-summary').value = dailySummary;
    } else {
        document.getElementById('edit-daily-summary').value = '';
    }
    
    // 加载周总结（如果是周日）
    const selectedDate = new Date(currentFilterDate);
    const dayOfWeek = selectedDate.getDay();
    if (dayOfWeek === 0) {
        const weekStart = new Date(selectedDate);
        // 调整到本周的开始（星期一），与saveEditedWeekSummary函数逻辑一致
        const daysToMonday = 6; // 周日距离周一有6天
        weekStart.setDate(selectedDate.getDate() - daysToMonday);
        const weekStartStr = `${weekStart.getFullYear()}-${String(weekStart.getMonth() + 1).padStart(2, '0')}-${String(weekStart.getDate()).padStart(2, '0')}`;
        const weekSummary = localStorage.getItem(`week-summary-${weekStartStr}`);
        if (weekSummary) {
            document.getElementById('edit-week-summary').value = weekSummary;
        } else {
            document.getElementById('edit-week-summary').value = '';
        }
    }
    
    // 加载月总结（如果是月末）
    const dayOfMonth = selectedDate.getDate();
    const month = selectedDate.getMonth();
    const year = selectedDate.getFullYear();
    const nextDay = new Date(selectedDate);
    nextDay.setDate(dayOfMonth + 1);
    const isMonthEnd = nextDay.getMonth() !== month;
    if (isMonthEnd) {
        const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;
        const monthSummary = localStorage.getItem(`month-summary-${monthStr}`);
        if (monthSummary) {
            document.getElementById('edit-month-summary').value = monthSummary;
        } else {
            document.getElementById('edit-month-summary').value = '';
        }
    }
    
    // 加载年度总结（如果是年末）
    const isYearEnd = (month === 11 && dayOfMonth === 31);
    if (isYearEnd) {
        const yearSummary = localStorage.getItem(`year-summary-${year}`);
        if (yearSummary) {
            document.getElementById('edit-year-summary').value = yearSummary;
        } else {
            document.getElementById('edit-year-summary').value = '';
        }
    }
}

// 保存编辑的每日总结
function saveEditedDailySummary() {
    const summary = document.getElementById('edit-daily-summary').value;
    localStorage.setItem(`daily-summary-${currentFilterDate}`, summary);
    alert('每日总结已保存');
}

// 保存编辑的周总结
function saveEditedWeekSummary() {
    const selectedDate = new Date(currentFilterDate);
    const weekStart = new Date(selectedDate);
    // 调整到本周的开始（星期一），与getPastWeeks函数逻辑一致
    const dayOfWeek = selectedDate.getDay();
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    weekStart.setDate(selectedDate.getDate() - daysToMonday);
    const weekStartStr = `${weekStart.getFullYear()}-${String(weekStart.getMonth() + 1).padStart(2, '0')}-${String(weekStart.getDate()).padStart(2, '0')}`;
    const summary = document.getElementById('edit-week-summary').value;
    localStorage.setItem(`week-summary-${weekStartStr}`, summary);
    alert('周总结已保存');
}

// 保存编辑的月度总结
function saveEditedMonthSummary() {
    const selectedDate = new Date(currentFilterDate);
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;
    const summary = document.getElementById('edit-month-summary').value;
    localStorage.setItem(`month-summary-${monthStr}`, summary);
    alert('月度总结已保存');
}

// 保存编辑的年度总结
function saveEditedYearSummary() {
    const selectedDate = new Date(currentFilterDate);
    const year = selectedDate.getFullYear();
    const summary = document.getElementById('edit-year-summary').value;
    localStorage.setItem(`year-summary-${year}`, summary);
    alert('年度总结已保存');
}

// 初始化应用
function getAuthSession() {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) {
        return null;
    }
    try {
        return JSON.parse(raw);
    } catch (error) {
        return null;
    }
}

function setAuthSession(session) {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

function clearAuthSession() {
    localStorage.removeItem(AUTH_STORAGE_KEY);
}

function isAuthenticated() {
    const session = getAuthSession();
    return !!(session && session.accessToken);
}

function getApiBaseUrl() {
    const input = document.getElementById('api-base-url');
    if (input && input.value.trim()) {
        return input.value.trim().replace(/\/$/, '');
    }
    return (localStorage.getItem('api-base-url') || API_BASE_URL).replace(/\/$/, '');
}

function persistApiBaseUrl() {
    localStorage.setItem('api-base-url', getApiBaseUrl());
}

async function apiRequest(path, options = {}) {
    const session = getAuthSession();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };

    if (session && session.accessToken && headers.Authorization !== '') {
        headers.Authorization = `Bearer ${session.accessToken}`;
    } else if (headers.Authorization === '') {
        delete headers.Authorization;
    }

    const response = await fetch(`${getApiBaseUrl()}${path}`, {
        ...options,
        headers
    });

    const contentType = response.headers.get('content-type') || '';
    const payload = contentType.includes('application/json')
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        const message = typeof payload === 'string'
            ? payload
            : payload.error || payload.detail || `Request failed with status ${response.status}`;
        throw new Error(message);
    }

    return payload;
}

function scheduleToBackendPayload(schedule) {
    return {
        title: schedule.title,
        date: schedule.date,
        time_range: `${schedule.startTime}-${schedule.endTime}`,
        location: schedule.location || '',
        content: `${schedule.title} ${schedule.location || ''}`.trim()
    };
}

function scheduleFromBackend(item) {
    const range = (item.time_range || '').split('-');
    return {
        id: item.id,
        title: item.title || '',
        date: item.date || currentFilterDate,
        startTime: range[0] || '',
        endTime: range[1] || '',
        location: item.location || '',
        content: item.content || ''
    };
}

function saveSchedules() {
    if (!isAuthenticated()) {
        localStorage.setItem('schedules', JSON.stringify(schedules));
    }
}

async function loadSchedules() {
    if (!isAuthenticated()) {
        const storedSchedules = localStorage.getItem('schedules');
        schedules = storedSchedules ? JSON.parse(storedSchedules) : [];
        return;
    }

    try {
        const payload = await apiRequest('/api/schedule');
        schedules = Array.isArray(payload) ? payload.map(scheduleFromBackend) : [];
    } catch (error) {
        console.error(error);
        alert(`加载云端日程失败: ${error.message}`);
        schedules = [];
    }
}

async function addSchedule() {
    const title = document.getElementById('title').value;
    const date = document.getElementById('date').value;
    const startTime = document.getElementById('start-time').value;
    const endTime = document.getElementById('end-time').value;
    const location = document.getElementById('location').value;

    if (!locations.includes(location)) {
        locations.push(location);
        localStorage.setItem('locations', JSON.stringify(locations));
    }

    const draft = {
        title,
        date,
        startTime,
        endTime,
        location
    };

    try {
        if (isAuthenticated()) {
            const payload = scheduleToBackendPayload(draft);
            if (editingId) {
                const updated = await apiRequest(`/api/schedule/${editingId}`, {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                });
                const nextSchedule = scheduleFromBackend(updated);
                const index = schedules.findIndex(schedule => schedule.id === editingId);
                if (index !== -1) {
                    schedules[index] = nextSchedule;
                }
            } else {
                const created = await apiRequest('/api/schedule', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                schedules.push(scheduleFromBackend(created));
            }
        } else if (editingId) {
            const index = schedules.findIndex(schedule => schedule.id === editingId);
            if (index !== -1) {
                schedules[index] = {
                    ...schedules[index],
                    ...draft
                };
            }
        } else {
            schedules.push({
                id: Date.now().toString(),
                ...draft
            });
        }

        saveSchedules();
        renderSchedules();
        document.getElementById('schedule-modal').style.display = 'none';
        document.getElementById('schedule-form').reset();
        document.getElementById('location-dropdown').style.display = 'none';
        editingId = null;
    } catch (error) {
        alert(`保存日程失败: ${error.message}`);
    }
}

async function deleteSchedule(id) {
    if (!id) {
        const deleteModal = document.getElementById('delete-modal');
        id = deleteModal.dataset.scheduleId;
    }

    if (!id) {
        return;
    }

    try {
        if (isAuthenticated()) {
            await apiRequest(`/api/schedule/${id}`, { method: 'DELETE' });
        }
        schedules = schedules.filter(schedule => schedule.id !== id);
        saveSchedules();
        renderSchedules();
        hideDeleteModal();
    } catch (error) {
        alert(`删除日程失败: ${error.message}`);
    }
}

function renderSettingsContent() {
    const settingsContent = document.getElementById('settings-content');
    const session = getAuthSession();
    const statusText = session
        ? `已登录: ${session.email}`
        : '当前未登录，日程将保存在本地浏览器。';

    settingsContent.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:20px;">
            <div style="padding:16px; border-radius:12px; background:white; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h3 style="margin-bottom:12px;">后端连接</h3>
                <div style="display:flex; gap:10px; flex-wrap:wrap;">
                    <input id="api-base-url" type="text" value="${getApiBaseUrl()}" style="flex:1; min-width:240px; padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <button id="save-api-base-url" style="padding:10px 16px; border:none; border-radius:8px; background:#4FC3F7; color:white; cursor:pointer;">保存地址</button>
                </div>
                <p id="auth-status" style="margin-top:12px; color:#607D8B;">${statusText}</p>
                <div style="margin-top:12px;">
                    <button id="logout-btn" style="padding:10px 16px; border:none; border-radius:8px; background:#f44336; color:white; cursor:pointer; ${session ? '' : 'display:none;'}">退出登录</button>
                </div>
            </div>

            <div style="padding:16px; border-radius:12px; background:white; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h3 style="margin-bottom:12px;">发送验证码</h3>
                <div style="display:grid; gap:10px;">
                    <input id="code-email" type="email" placeholder="邮箱" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <div style="display:flex; gap:10px; flex-wrap:wrap;">
                        <button id="send-register-code-btn" style="padding:10px 16px; border:none; border-radius:8px; background:#4CAF50; color:white; cursor:pointer;">注册验证码</button>
                        <button id="send-reset-code-btn" style="padding:10px 16px; border:none; border-radius:8px; background:#FF9800; color:white; cursor:pointer;">重置验证码</button>
                    </div>
                </div>
            </div>

            <div style="padding:16px; border-radius:12px; background:white; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h3 style="margin-bottom:12px;">注册</h3>
                <div style="display:grid; gap:10px;">
                    <input id="register-email" type="email" placeholder="邮箱" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <input id="register-password" type="password" placeholder="密码" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <input id="register-code" type="text" placeholder="验证码" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <button id="register-btn" style="padding:10px 16px; border:none; border-radius:8px; background:#4CAF50; color:white; cursor:pointer;">注册并登录</button>
                </div>
            </div>

            <div style="padding:16px; border-radius:12px; background:white; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h3 style="margin-bottom:12px;">登录</h3>
                <div style="display:grid; gap:10px;">
                    <input id="login-email" type="email" placeholder="邮箱" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <input id="login-password" type="password" placeholder="密码" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <button id="login-btn" style="padding:10px 16px; border:none; border-radius:8px; background:#2196F3; color:white; cursor:pointer;">登录</button>
                </div>
            </div>

            <div style="padding:16px; border-radius:12px; background:white; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h3 style="margin-bottom:12px;">重置密码</h3>
                <div style="display:grid; gap:10px;">
                    <input id="reset-email" type="email" placeholder="邮箱" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <input id="reset-password" type="password" placeholder="新密码" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <input id="reset-code" type="text" placeholder="验证码" style="padding:10px; border:1px solid #ddd; border-radius:8px;">
                    <button id="reset-btn" style="padding:10px 16px; border:none; border-radius:8px; background:#9C27B0; color:white; cursor:pointer;">重置密码</button>
                </div>
            </div>
        </div>
    `;
}

function syncAuthStatusText() {
    const statusNode = document.getElementById('auth-status');
    const logoutBtn = document.getElementById('logout-btn');
    if (!statusNode || !logoutBtn) {
        return;
    }

    const session = getAuthSession();
    statusNode.textContent = session
        ? `已登录: ${session.email}，当前日程会和 Go 后端同步。`
        : '当前未登录，日程将保存在本地浏览器。';
    logoutBtn.style.display = session ? 'inline-flex' : 'none';
}

async function handleAuthSuccess(payload) {
    setAuthSession({
        userId: payload.user_id,
        email: payload.email,
        accessToken: payload.access_token
    });
    syncAuthStatusText();
    await loadSchedules();
    renderSchedules();
}

function setupSettingsActions() {
    const settingsContent = document.getElementById('settings-content');
    settingsContent.addEventListener('click', async function(event) {
        const target = event.target;
        if (!(target instanceof HTMLElement)) {
            return;
        }

        try {
            if (target.id === 'save-api-base-url') {
                persistApiBaseUrl();
                alert('后端地址已保存');
            }

            if (target.id === 'send-register-code-btn' || target.id === 'send-reset-code-btn') {
                const email = document.getElementById('code-email').value.trim();
                const type = target.id === 'send-register-code-btn' ? 'register' : 'reset';
                await apiRequest('/api/auth/send-code', {
                    method: 'POST',
                    headers: { Authorization: '' },
                    body: JSON.stringify({ email, type })
                });
                alert('验证码已发送或已在服务端生成');
            }

            if (target.id === 'register-btn') {
                const payload = await apiRequest('/api/auth/register', {
                    method: 'POST',
                    headers: { Authorization: '' },
                    body: JSON.stringify({
                        email: document.getElementById('register-email').value.trim(),
                        password: document.getElementById('register-password').value,
                        code: document.getElementById('register-code').value.trim()
                    })
                });
                await handleAuthSuccess(payload);
                alert('注册成功');
            }

            if (target.id === 'login-btn') {
                const payload = await apiRequest('/api/auth/login', {
                    method: 'POST',
                    headers: { Authorization: '' },
                    body: JSON.stringify({
                        email: document.getElementById('login-email').value.trim(),
                        password: document.getElementById('login-password').value
                    })
                });
                await handleAuthSuccess(payload);
                alert('登录成功');
            }

            if (target.id === 'reset-btn') {
                await apiRequest('/api/auth/reset-password', {
                    method: 'POST',
                    headers: { Authorization: '' },
                    body: JSON.stringify({
                        email: document.getElementById('reset-email').value.trim(),
                        new_password: document.getElementById('reset-password').value,
                        code: document.getElementById('reset-code').value.trim()
                    })
                });
                alert('密码重置成功');
            }

            if (target.id === 'logout-btn') {
                clearAuthSession();
                await loadSchedules();
                renderSettingsContent();
                syncAuthStatusText();
                alert('已退出登录');
            }
        } catch (error) {
            alert(error.message);
        }
    });
}

async function init() {
    loadLocations();
    updateDateDisplay();
    checkForPeriodicSummaries();
    setupEventListeners();
    loadTodoContent();
    renderSettingsContent();
    setupSettingsActions();
    await loadSchedules();
    renderSchedules();
    syncAuthStatusText();
    document.getElementById('todo-modal').style.display = 'block';
}

init();
