/**
 * Graph2plan Wizard 步驟控制 (4 步驟版)
 */

var currentStep = 1;
var completedSteps = [];
var TOTAL_STEPS = 4;

// 頁面載入完成後初始化
$(document).ready(function () {
    // 初始化 - 顯示第一步
    showStep(1);

    // 注意：Init 已在 buttonEvent.js 中呼叫，這裡不重複呼叫
});

/**
 * 顯示指定步驟
 */
function showStep(step) {
    // 隱藏所有步驟內容
    $('.step-content').removeClass('active');

    // 顯示目標步驟
    $('#step' + step).addClass('active');

    // 更新導覽列狀態
    $('.step-item').removeClass('active');
    $('.step-item[data-step="' + step + '"]').addClass('active');

    currentStep = step;
}

/**
 * 跳轉到指定步驟（需檢查權限）
 */
function goToStep(step) {
    var item = $('.step-item[data-step="' + step + '"]');

    // 如果是禁用狀態，不允許跳轉
    if (item.hasClass('disabled')) {
        return;
    }

    showStep(step);
}

/**
 * 完成當前步驟並進入下一步
 */
function completeStep(step) {
    // Step 2 -> Step 3: 自動執行 Transfer
    if (step === 2) {
        // 檢查是否已選擇結果
        if (typeof selectedRooms === 'undefined' || selectedRooms === null ||
            typeof selectedRoomID === 'undefined' || selectedRoomID === null) {
            alert('請先在 Results 中選擇一個格局再繼續');
            return;
        }

        // 清除 LeftGraphSVG 中的舊元素
        d3.select('body').select('#LeftGraphSVG').selectAll('.TransLine').remove();
        d3.select('body').select('#LeftGraphSVG').selectAll('.TransCircle').remove();

        // 執行 Transfer，將選擇的結果轉換到 Input Graph
        CreateLeftGraph(selectedRooms, selectedRoomID);

        // 設置 isTrans 標記
        isTrans = 1;
    }

    // 標記為已完成
    if (completedSteps.indexOf(step) === -1) {
        completedSteps.push(step);
    }

    // 更新 UI 狀態
    var currentItem = $('.step-item[data-step="' + step + '"]');
    currentItem.addClass('completed');

    // 解鎖下一步
    var nextStep = step + 1;
    if (nextStep <= TOTAL_STEPS) {
        var nextItem = $('.step-item[data-step="' + nextStep + '"]');
        nextItem.removeClass('disabled');

        // 跳轉到下一步
        showStep(nextStep);
    }
}

/**
 * Wizard 專用的 Load 檔案函數
 */
function wizardLoadFile(files) {
    // 呼叫原有的載入函數
    LoadTestBoundary(files);

    // 完成第一步，進入第二步
    setTimeout(function () {
        completeStep(1);
    }, 500);
}

/**
 * Wizard 專用的 Number Search
 */
function wizardNumSearch() {
    NumSearch();

    // 不自動跳轉，讓使用者在同一頁面查看結果
}

/**
 * Wizard 專用的 Graph Search
 */
function wizardGraphSearch() {
    GraphSearch();
}

/**
 * 覆蓋原有的 show 函數（Wizard 模式不需要透明度控制）
 */
function show(isShow) {
    // Wizard 模式下不需要透明度控制
    // 保持所有元素可見
}
