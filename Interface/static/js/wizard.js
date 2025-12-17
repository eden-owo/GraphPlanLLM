/**
 * Graph2plan Wizard 步驟控制 (4 步驟版)
 */

var currentStep = 1;
var completedSteps = [];
var TOTAL_STEPS = 4;
var llmGraphResult = null;  // 儲存 LLM Graph 生成的結果

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
            alert('請先在 Results 中選擇一個格局，或使用 LLM Graph Generation 再繼續');
            return;
        }

        // 清除 LeftGraphSVG 中的舊元素
        d3.select('body').select('#LeftGraphSVG').selectAll('.TransLine').remove();
        d3.select('body').select('#LeftGraphSVG').selectAll('.TransCircle').remove();

        // 如果是 LLM 生成的 Graph，跳過 TransGraph 呼叫 (佈局已經生成)
        if (selectedRoomID === 'llm_generated') {
            console.log('LLM Graph 已包含佈局，複製到 Step 3');

            // 複製 LLM 生成的佈局到 Step 3 的 LeftGraphSVG
            if (typeof llmGraphResult !== 'undefined' && llmGraphResult !== null) {
                copyLLMToLeftGraph(llmGraphResult);
                // 設置 Generate 按鈕處理器
                setupLLMGenerateHandler(llmGraphResult);
            }

            // 設置 isTrans 標記
            isTrans = 1;
        } else {
            // 執行 Transfer，將選擇的結果轉換到 Input Graph
            CreateLeftGraph(selectedRooms, selectedRoomID);

            // 設置 isTrans 標記
            isTrans = 1;
        }
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
 * Wizard 專用的 Load 範例函數
 */
function wizardLoadExample() {
    // 取得範例列表，載入第一個範例
    $.getJSON("/index/GetExampleList/", function (examples) {
        if (examples && examples.length > 0) {
            var exampleName = examples[0];

            // 設置 cookie
            document.cookie = "hsname=" + exampleName;

            // 清空現有的 SVG
            d3.select('body').select('#LeftBaseSVG').selectAll("svg > *").remove();
            d3.select('body').select('#LeftGraphSVG').selectAll("svg > *").remove();
            d3.select('body').select('#LeftLayoutSVG').selectAll("svg > *").remove();
            d3.select('body').select('#RightLayoutSVG').selectAll("svg > *").remove();
            d3.select('body').select('#RightSVG').selectAll("svg > *").remove();

            // 載入範例邊界
            $.get("/index/LoadTestBoundary", { 'testName': exampleName }, function (ret) {
                var border = 4;
                islLoadTest = 1;
                var hsex = ret['exterior'];
                userBoundaryExterior = hsex;
                userBoundaryDoor = ret['door'];

                // 繪製邊界到 LeftBaseSVG
                d3.select("#LeftBaseSVG")
                    .append("polygon")
                    .attr("points", hsex)
                    .attr("fill", "none")
                    .attr("stroke", roomcolor("Exterior wall"))
                    .attr("stroke-width", border);

                var door = ret['door'].split(",");
                d3.select('body').select('#LeftBaseSVG').append('line')
                    .attr("x1", parseInt(door[0]))
                    .attr("y1", door[1])
                    .attr("x2", door[2])
                    .attr("y2", door[3])
                    .attr("stroke", roomcolor("Front door"))
                    .attr("stroke-width", border);

                // 繪製到 PredictLayoutSVG
                d3.select('body').select('#PredictLayoutSVG').selectAll('*').remove();
                d3.select('body').select('#PredictSVG').selectAll('*').remove();
                d3.select("#PredictLayoutSVG")
                    .append("polygon")
                    .attr("points", hsex)
                    .attr("fill", "none")
                    .attr("stroke", roomcolor("Exterior wall"))
                    .attr("stroke-width", border);
                d3.select('#PredictLayoutSVG').append('line')
                    .attr("x1", parseInt(door[0]))
                    .attr("y1", door[1])
                    .attr("x2", door[2])
                    .attr("y2", door[3])
                    .attr("stroke", roomcolor("Front door"))
                    .attr("stroke-width", border);

                d3.select('body').select('#LeftBaseSVG').style("transform", "translateX(-50%) scale(1.5)");
                d3.select('body').select('#LeftGraphSVG').style("transform", "translateX(-50%) scale(1.5)");
                d3.select('body').select('#PredictLayoutSVG').style("transform", "translateX(-50%) scale(1.5)");
                d3.select('body').select('#PredictSVG').style("transform", "translateX(-50%) scale(1.5)");

                // 執行 NumSearch
                NumSearch();

                // 完成第一步，進入第二步
                setTimeout(function () {
                    completeStep(1);
                }, 500);
            });
        } else {
            alert("沒有可用的範例");
        }
    }).fail(function () {
        alert("載入範例失敗");
    });
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

// ========== LLM Graph Generation ==========

/**
 * LLM Graph Generation - 使用 LLM 從自然語言生成格局圖
 */
function wizardLLMGraph() {
    var prompt = document.getElementById('llmGraphPrompt').value.trim();

    if (!prompt) {
        alert('請輸入格局描述');
        return;
    }

    // 取得上傳的檔案名稱
    var hsname = null;
    var arr, reg = new RegExp("(^| )hsname=([^;]*)(;|$)");
    if (arr = document.cookie.match(reg)) {
        hsname = arr[2];
    }

    if (!hsname) {
        alert('請先在 Step 1 上傳邊界檔案');
        return;
    }

    console.log('=== LLM Graph Generation Request ===');
    console.log('Prompt:', prompt);
    console.log('TestName:', hsname);

    // 顯示 loading 狀態
    var btn = document.getElementById('llmGraphBtn');
    var originalText = btn.innerHTML;
    btn.innerHTML = '⏳ 生成中...';
    btn.disabled = true;

    // 呼叫後端 API
    $.ajax({
        url: '/index/LLMGenerateGraph/',
        method: 'GET',
        data: {
            prompt: prompt,
            testName: hsname
        },
        success: function (ret) {
            console.log('LLM Graph Response:', ret);

            // 恢復按鈕
            btn.innerHTML = originalText;
            btn.disabled = false;

            // 隱藏 placeholder
            $('#rightbox .placeholder-text').hide();

            // 清空現有的結果
            d3.select('body').select('#RightLayoutSVG').selectAll('*').remove();
            d3.select('body').select('#RightSVG').selectAll('*').remove();
            d3.select('body').select('#PredictLayoutSVG').selectAll('*').remove();
            d3.select('body').select('#PredictSVG').selectAll('*').remove();

            // 繪製生成的 Graph 到 RightSVG (Output Graph)
            drawLLMGraph(ret);

            // 繪製到 PredictSVG (Transfer Result)
            drawLLMGraphPredict(ret);

            // 儲存 LLM 結果供 Step 3 使用
            llmGraphResult = ret;

            // 保存選中的數據供後續使用
            selectedRooms = [hsname];
            selectedRoomID = 'llm_generated';

            // 顯示成功訊息
            console.log('LLM Graph 生成成功!');
            console.log('節點:', ret.llm_nodes);
            console.log('邊:', ret.llm_edges);
        },
        error: function (xhr, status, error) {
            // 恢復按鈕
            btn.innerHTML = originalText;
            btn.disabled = false;

            var errorMsg = 'LLM Graph 生成失敗';
            if (xhr.responseJSON && xhr.responseJSON.error) {
                errorMsg = xhr.responseJSON.error;
            }
            alert(errorMsg);
            console.error('LLM Graph Error:', error);
        }
    });
}

/**
 * 繪製 LLM 生成的 Graph 到 RightSVG (Output Graph)
 */
function drawLLMGraph(ret) {
    var border = 4;

    // 繪製邊 (lines)
    for (var i = 0; i < ret.hsedge.length; i++) {
        var roomA = ret.hsedge[i][0];
        var roomB = ret.hsedge[i][1];

        d3.select('body').select('#RightSVG').append('line')
            .attr("x1", ret.rmpos[roomA][2])
            .attr("y1", ret.rmpos[roomA][3])
            .attr("x2", ret.rmpos[roomB][2])
            .attr("y2", ret.rmpos[roomB][3])
            .attr("stroke", "#000000")
            .attr("stroke-width", "2px")
            .attr("id", ret.rmpos[roomA][1] + "-" + ret.rmpos[roomB][1]);
    }

    // 繪製節點 (circles)
    for (var i = 0; i < ret.rmpos.length; i++) {
        d3.select('body').select('#RightSVG').append('circle')
            .attr("cx", ret.rmpos[i][2])
            .attr("cy", ret.rmpos[i][3])
            .attr("fill", roomcolor(ret.rmpos[i][1]))
            .attr("r", ret.rmsize[i][0])
            .attr("stroke", "#000000")
            .attr("stroke-width", 2)
            .attr("id", (i + 1) + "-" + ret.rmpos[i][1])
            .append("title")
            .text(ret.rmpos[i][1]);
    }

    d3.select('body').select('#RightSVG').style("transform", "translateX(-50%) scale(1.5)");

    // 繪製邊界到 RightLayoutSVG
    d3.select("#RightLayoutSVG")
        .append("polygon")
        .attr("points", ret.exterior)
        .attr("fill", "none")
        .attr("stroke", roomcolor("Exterior wall"))
        .attr("stroke-width", border);

    // 繪製大門
    var door = ret.door.split(",");
    d3.select('body').select('#RightLayoutSVG').append('line')
        .attr("x1", door[0])
        .attr("y1", door[1])
        .attr("x2", door[2])
        .attr("y2", door[3])
        .attr("stroke", roomcolor("Front door"))
        .attr("stroke-width", border);

    d3.select('body').select('#RightLayoutSVG').style("transform", "translateX(-50%) scale(1.5)");
}

/**
 * 繪製 LLM 生成的 Graph 到 PredictSVG (Transfer Result)
 */
function drawLLMGraphPredict(ret) {
    var border = 4;
    var interiorwall_color = roomcolor("Interior wall");

    // 如果有房間佈局，先繪製房間矩形
    if (ret.has_layout && ret.roomret) {
        for (var i = 0; i < ret.roomret.length; i++) {
            var room = ret.roomret[i];
            var rx = room[0][0];
            var ry = room[0][1];
            var rw = room[0][2] - room[0][0];
            var rh = room[0][3] - room[0][1];
            var roomType = room[1][0];
            var color = roomcolor(roomType);

            d3.select("#PredictLayoutSVG").append("rect")
                .attr("x", rx)
                .attr("y", ry)
                .attr("width", rw)
                .attr("height", rh)
                .attr("stroke-width", border)
                .attr("stroke", interiorwall_color)
                .attr("fill", color)
                .attr("id", "LLM_" + roomType + "_" + i)
                .append("title")
                .text(roomType);
        }

        // 繪製室內門
        if (ret.indoor) {
            for (var i = 0; i < ret.indoor.length; i++) {
                d3.select("#PredictLayoutSVG").append("rect")
                    .attr("x", ret.indoor[i][0])
                    .attr("y", ret.indoor[i][1])
                    .attr("width", ret.indoor[i][2])
                    .attr("height", ret.indoor[i][3])
                    .attr("fill", roomcolor("Interior door"));
            }
        }
    }

    // 使用邊界作為 clip path
    d3.select("#PredictLayoutSVG").append("clipPath")
        .attr("id", "LLMPredictclip-th")
        .append("polygon")
        .attr("points", ret.exterior);
    d3.select("#PredictLayoutSVG").attr("clip-path", "url(#LLMPredictclip-th)");

    // 繪製邊界
    d3.select("#PredictLayoutSVG")
        .append("polygon")
        .attr("points", ret.exterior)
        .attr("fill", "none")
        .attr("stroke", roomcolor("Exterior wall"))
        .attr("stroke-width", border);

    // 繪製大門
    var door = ret.door.split(",");
    d3.select('#PredictLayoutSVG').append('line')
        .attr("x1", door[0])
        .attr("y1", door[1])
        .attr("x2", door[2])
        .attr("y2", door[3])
        .attr("stroke", roomcolor("Front door"))
        .attr("stroke-width", border);

    // 繪製窗戶
    if (ret.windows) {
        var wincolor = d3.rgb(195, 195, 195);
        for (var i = 0; i < ret.windows.length; i++) {
            d3.select("#PredictLayoutSVG").append("rect")
                .attr("x", ret.windows[i][0])
                .attr("y", ret.windows[i][1])
                .attr("width", ret.windows[i][2])
                .attr("height", ret.windows[i][3])
                .attr("fill", "#ffffff")
                .attr("stroke", wincolor)
                .attr("stroke-width", 1);
        }
    }

    // 繪製邊 (lines) - 在節點圖層
    for (var i = 0; i < ret.hsedge.length; i++) {
        var roomA = ret.hsedge[i][0];
        var roomB = ret.hsedge[i][1];

        d3.select('body').select('#PredictSVG').append('line')
            .attr("x1", ret.rmpos[roomA][2])
            .attr("y1", ret.rmpos[roomA][3])
            .attr("x2", ret.rmpos[roomB][2])
            .attr("y2", ret.rmpos[roomB][3])
            .attr("stroke", "#000000")
            .attr("stroke-width", "2px")
            .attr("class", "PredictTransLine");
    }

    // 繪製節點 (circles) - 在節點圖層
    for (var i = 0; i < ret.rmpos.length; i++) {
        d3.select('body').select('#PredictSVG').append('circle')
            .attr("cx", ret.rmpos[i][2])
            .attr("cy", ret.rmpos[i][3])
            .attr("fill", roomcolor(ret.rmpos[i][1]))
            .attr("r", ret.rmsize[i][0])
            .attr("stroke", "#000000")
            .attr("stroke-width", 2)
            .attr("class", "PredictTransCircle")
            .append("title")
            .text(ret.rmpos[i][1]);
    }

    d3.select('body').select('#PredictLayoutSVG').style("transform", "translateX(-50%) scale(1.5)");
    d3.select('body').select('#PredictSVG').style("transform", "translateX(-50%) scale(1.5)");
}


/**
 * 複製 LLM 生成的佈局到 Step 3 的 LeftGraphSVG
 */
function copyLLMToLeftGraph(ret) {
    var border = 4;
    var interiorwall_color = roomcolor("Interior wall");

    // 清除 Step 3 的舊內容
    d3.select('body').select('#LeftLayoutSVG').selectAll('*').remove();
    d3.select('body').select('#LeftGraphSVG').selectAll('*').remove();

    // 如果有房間佈局，繪製房間矩形
    if (ret.has_layout && ret.roomret) {
        for (var i = 0; i < ret.roomret.length; i++) {
            var room = ret.roomret[i];
            var rx = room[0][0];
            var ry = room[0][1];
            var rw = room[0][2] - room[0][0];
            var rh = room[0][3] - room[0][1];
            var roomType = room[1][0];
            var color = roomcolor(roomType);

            d3.select("#LeftLayoutSVG").append("rect")
                .attr("x", rx)
                .attr("y", ry)
                .attr("width", rw)
                .attr("height", rh)
                .attr("stroke-width", border)
                .attr("stroke", interiorwall_color)
                .attr("fill", color)
                .attr("id", "LeftLLM_" + roomType + "_" + i)
                .append("title")
                .text(roomType);
        }
    }

    // 繪製邊界
    d3.select("#LeftLayoutSVG")
        .append("polygon")
        .attr("points", ret.exterior)
        .attr("fill", "none")
        .attr("stroke", roomcolor("Exterior wall"))
        .attr("stroke-width", border);

    // 繪製大門
    var door = ret.door.split(",");
    d3.select('#LeftLayoutSVG').append('line')
        .attr("x1", door[0])
        .attr("y1", door[1])
        .attr("x2", door[2])
        .attr("y2", door[3])
        .attr("stroke", roomcolor("Front door"))
        .attr("stroke-width", border);

    // 計算節點位置 - 如果有 roomret，使用房間中心座標
    var nodePositions = [];
    if (ret.has_layout && ret.roomret) {
        // 從 roomret 計算房間中心作為節點位置
        for (var i = 0; i < ret.roomret.length; i++) {
            var room = ret.roomret[i];
            var centerX = (room[0][0] + room[0][2]) / 2;
            var centerY = (room[0][1] + room[0][3]) / 2;
            nodePositions.push({ x: centerX, y: centerY, type: room[1][0], idx: i });
        }
    } else {
        // 沒有 roomret，使用原始 rmpos
        for (var i = 0; i < ret.rmpos.length; i++) {
            nodePositions.push({ x: ret.rmpos[i][2], y: ret.rmpos[i][3], type: ret.rmpos[i][1], idx: i });
        }
    }

    // 繪製邊 (lines) - 使用 CreateLine 函數以啟用事件處理
    for (var i = 0; i < ret.hsedge.length; i++) {
        var roomA = ret.hsedge[i][0];
        var roomB = ret.hsedge[i][1];
        var lineId = "TransLine_" + roomA + "_" + roomB + "_0";

        // 使用計算後的節點位置
        var posA = nodePositions[roomA] || { x: 0, y: 0 };
        var posB = nodePositions[roomB] || { x: 0, y: 0 };

        // 使用 CreateLine 函數（如果存在），否則直接創建
        if (typeof CreateLine === 'function') {
            CreateLine(posA.x, posA.y, posB.x, posB.y, lineId);
        } else {
            d3.select('body').select('#LeftGraphSVG').append('line')
                .attr("x1", posA.x)
                .attr("y1", posA.y)
                .attr("x2", posB.x)
                .attr("y2", posB.y)
                .attr("stroke", "#000000")
                .attr("stroke-width", "2px")
                .attr("id", lineId)
                .attr("class", "TransLine");
        }
    }

    // 繪製節點 (circles) - 使用 CreateCircle 函數以啟用拖曳和編輯事件
    for (var i = 0; i < nodePositions.length; i++) {
        var pos = nodePositions[i];
        var circleId = "TransCircle_" + pos.idx + "_" + pos.type;
        var nodeSize = (ret.rmsize[i] && ret.rmsize[i][0]) || 8;

        // 使用 CreateCircle 函數（如果存在），否則直接創建
        if (typeof CreateCircle === 'function') {
            CreateCircle(pos.x, pos.y, circleId, nodeSize);
            // 設置 scalesize 屬性
            d3.select("body").select("#LeftGraphSVG").select("#" + circleId).attr('scalesize', 1);
        } else {
            d3.select('body').select('#LeftGraphSVG').append('circle')
                .attr("cx", pos.x)
                .attr("cy", pos.y)
                .attr("fill", roomcolor(pos.type))
                .attr("r", nodeSize)
                .attr("stroke", "#000000")
                .attr("stroke-width", 2)
                .attr("id", circleId)
                .attr("class", "TransCircle")
                .attr("scalesize", 1)
                .append("title")
                .text(pos.type);
        }
    }

    // 設置 clip-path (與 CreateLeftPlan 一致)
    d3.select("#LeftLayoutSVG").append("clipPath")
        .attr("id", "llm-clip-th")
        .append("polygon")
        .attr("points", ret.exterior);
    d3.select("#LeftLayoutSVG").attr("clip-path", "url(#llm-clip-th)");

    // 設置 transform (與 CreateLeftPlan 一致)
    d3.select('body').select('#LeftLayoutSVG').style("transform", "translateX(-50%) scale(1.5)");
    d3.select('body').select('#LeftGraphSVG').style("transform", "translateX(-50%) scale(1.5)");

    // 設置房間數量 cookie
    document.cookie = "RoomNum=" + ret.rmpos.length;

    console.log('LLM Graph 已複製到 Step 3，節點可編輯');
}


/**
 * 設置 LLM Graph 的 Generate 按鈕處理器
 */
function setupLLMGenerateHandler(ret) {
    var hsname = null;
    var arr, reg = new RegExp("(^| )hsname=([^;]*)(;|$)");
    if (arr = document.cookie.match(reg)) {
        hsname = arr[2];
    }

    document.getElementById("Generate").onclick = function () {
        console.log('LLM Generate clicked');

        // 取得編輯後的 Graph
        var editedGraph = GetEditGraph(ret.rmpos);

        // 提取節點和邊資訊
        var nodes = [];
        var edges = [];
        var positions = [];

        // 從 LeftGraphSVG 讀取當前節點狀態
        var circles = d3.select("body").select("#LeftGraphSVG").selectAll("circle");
        circles.each(function (d, i) {
            var idParts = this.id.split("_");
            if (idParts.length >= 3) {
                var roomType = idParts[2];
                nodes.push(roomType);
                positions.push([this.cx.animVal.value, this.cy.animVal.value]);
            }
        });

        // 讀取邊資訊
        var lines = d3.select("body").select("#LeftGraphSVG").selectAll(".TransLine");
        lines.each(function (d, i) {
            var idParts = this.id.split("_");
            if (idParts.length >= 3) {
                edges.push([parseInt(idParts[1]), parseInt(idParts[2])]);
            }
        });

        console.log('LLM Regenerate - nodes:', nodes);
        console.log('LLM Regenerate - edges:', edges);
        console.log('LLM Regenerate - positions:', positions);

        // 呼叫後端 API 重新生成佈局
        $.ajax({
            url: '/index/LLMRegenerateLayout/',
            method: 'GET',
            data: {
                testName: hsname,
                nodes: JSON.stringify(nodes),
                edges: JSON.stringify(edges),
                positions: JSON.stringify(positions)
            },
            success: function (result) {
                console.log('LLM Regenerate result:', result);

                // 更新 LeftLayoutSVG 顯示新的房間佈局
                if (result.roomret) {
                    CreateLeftPlan(result.roomret, result.exterior, result.door,
                        result.windows || [], result.indoor || [], result.windowsline || []);

                    // 更新節點大小
                    if (result.rmsize) {
                        for (var i = 0; i < result.rmsize.length; i++) {
                            var circleId = "TransCircle_" + i + "_" + (result.rmpos ? result.rmpos[i][1] : nodes[i]);
                            var circle = d3.select("body").select("#LeftGraphSVG").select("#" + circleId);
                            if (!circle.empty() && result.rmsize[i]) {
                                circle.attr("r", result.rmsize[i][0] || 5);
                            }
                        }
                    }
                }
            },
            error: function (xhr, status, error) {
                console.error('LLM Regenerate error:', error);
                alert('重新生成佈局失敗: ' + (xhr.responseJSON ? xhr.responseJSON.error : error));
            }
        });
    };

    // 設置 downLoad 按鈕處理器
    document.getElementById("downLoad").onclick = function () {
        var arr, reg = new RegExp("(^| )hsname=([^;]*)(;|$)");
        if (arr = document.cookie.match(reg))
            hsname = arr[2];

        console.log('LLM Download clicked, hsname:', hsname);

        // 取得編輯後的佈局和圖形
        var NewLay = GetEditLayout();
        var newGraph = GetEditGraph(ret.rmpos);

        // 呼叫 LLM 專用的儲存 API
        $.get("/index/LLMSaveLayout/", {
            'NewLay': JSON.stringify(NewLay),
            'NewGraph': JSON.stringify(newGraph),
            'userRoomID': hsname.split('.')[0]
        }, function (flag) {
            console.log('LLM Save result:', flag);

            // 下載 .mat 檔案
            var link = document.createElement('a');
            link.href = "../static/" + hsname.split(".")[0] + ".mat";
            var event = document.createEvent('MouseEvents');
            event.initMouseEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
            link.dispatchEvent(event);
        });
    };

    console.log('LLM Generate handler 已設置');
}

