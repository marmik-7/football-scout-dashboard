/* Ensure Dash dcc.Graph charts resize cleanly to their container width (including post-mount layout transitions) */
(function () {
    var observedContainers = new WeakSet();
    var pendingNudge = new WeakSet();

    function checkAndResize(container) {
        if (!container || container.clientWidth <= 0) {
            return;
        }
        var graph = container.querySelector(".dash-graph");
        var svg = container.querySelector("svg.main-svg");
        if (!graph || !svg) {
            return;
        }

        var svgWidth = parseFloat(svg.getAttribute("width") || "0");
        var containerWidth = container.clientWidth;

        // If Plotly rendered wider than its card container (e.g. during AppShell breakpoint transition),
        // nudge the .dash-graph width so Dash's internal ResizeSensor invokes Plotly.Plots.resize().
        if (Math.abs(svgWidth - containerWidth) > 4 && !pendingNudge.has(graph)) {
            pendingNudge.add(graph);
            graph.style.width = Math.max(100, containerWidth - 1) + "px";
            requestAnimationFrame(function () {
                setTimeout(function () {
                    graph.style.width = "100%";
                    window.dispatchEvent(new Event("resize"));
                    setTimeout(function () {
                        pendingNudge.delete(graph);
                    }, 120);
                }, 40);
            });
        }
    }

    function scanAll() {
        var containers = document.querySelectorAll(".scout-chart-container");
        containers.forEach(function (container) {
            if (typeof ResizeObserver !== "undefined" && !observedContainers.has(container)) {
                observedContainers.add(container);
                var ro = new ResizeObserver(function () {
                    checkAndResize(container);
                });
                ro.observe(container);
            }
            checkAndResize(container);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", scanAll);
    } else {
        scanAll();
    }

    var mo = new MutationObserver(function () {
        scanAll();
        setTimeout(scanAll, 250);
        setTimeout(scanAll, 1000);
    });
    mo.observe(document.documentElement, { childList: true, subtree: true });
    window.addEventListener("load", function () {
        setTimeout(scanAll, 500);
        setTimeout(scanAll, 1500);
    });
})();
