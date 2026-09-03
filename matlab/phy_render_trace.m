function phy_render_trace(tracePath, nodeId, imagePath, visibleFigure)
%PHY_RENDER_TRACE Render a node's input and output entirely in MATLAB.

if nargin < 4, visibleFigure = false; end
loaded = load(tracePath, 'trace');
t = loaded.trace;
limit = 1000;
visibility = 'off';
if visibleFigure, visibility = 'on'; end
fig = figure('Visible', visibility, 'Color', [0.94 0.94 0.94], ...
    'Name', ['PHY Debugger — ' nodeId], 'NumberTitle', 'off', ...
    'Position', [100 100 1200 520]);
tiles = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
title(tiles, sprintf('%s · %s · E_b/N_0 = %.1f dB', ...
    upper(nodeId), t.config.modulation, t.config.ebnoDb), ...
    'Color', [0.10 0.10 0.10], 'FontWeight', 'bold');

switch nodeId
    case 'source'
        leftSeries(t.sourceInput, ['INPUT · ' t.sourceInputLabel], limit);
        bitSeries(t.sourceBits, 'OUTPUT · Information bits', limit);
    case 'group'
        bitSeries(t.sourceBits, 'INPUT · Serial bits', limit);
        groupImage(t.bitGroups, 'OUTPUT · Bit words');
    case 'mapper'
        groupImage(t.bitGroups, 'INPUT · Bit words');
        constellationPlot(t.txSymbols, t.constellation, 'OUTPUT · Transmitted symbols', limit);
    case 'channel'
        constellationPlot(t.txSymbols, t.constellation, 'INPUT · Transmitted symbols', limit);
        constellationPlot(t.rxSymbols, t.constellation, 'OUTPUT · Received symbols', limit);
    case 'detector'
        constellationPlot(t.rxSymbols, t.constellation, 'INPUT · Received symbols', limit);
        groupImage(t.detectedGroups, 'OUTPUT · Detected bit words');
    case 'sink'
        compareBits(t.sourceBits, t.recoveredBits, limit);
        errorPlot(t.errorMask, t.ber, t.bitErrors, limit);
    otherwise
        close(fig);
        error('Unknown node: %s', nodeId);
end

if ~isempty(imagePath)
    exportgraphics(fig, imagePath, 'Resolution', 150, ...
        'BackgroundColor', [0.94 0.94 0.94]);
end
if ~visibleFigure, close(fig); end
end


function prepareAxis(titleText)
ax = gca;
ax.Color = [1 1 1];
ax.XColor = [0.15 0.15 0.15];
ax.YColor = [0.15 0.15 0.15];
ax.GridColor = [0.55 0.55 0.55];
ax.GridAlpha = 0.25;
title(titleText, 'Color', [0.10 0.10 0.10], 'FontWeight', 'bold');
grid on;
end


function leftSeries(x, titleText, limit)
nexttile;
n = min(numel(x), limit);
plot(1:n, double(x(1:n)), 'Color', [0 0.4470 0.7410], 'LineWidth', 1.2);
xlabel('Index'); ylabel('Value'); prepareAxis(titleText);
end


function bitSeries(bits, titleText, limit)
nexttile;
n = min(numel(bits), limit);
stairs(1:n, double(bits(1:n)), 'Color', [0 0.4470 0.7410], 'LineWidth', 1.2);
ylim([-0.2 1.2]); xlabel('Bit index'); ylabel('Bit'); prepareAxis(titleText);
end


function groupImage(groups, titleText)
nexttile;
n = min(size(groups,1), 160);
imagesc(double(groups(1:n,:)).');
colormap(gca, [1 1 1; 0 0.4470 0.7410]);
xlabel('Symbol index'); ylabel('Bit position'); prepareAxis(titleText);
end


function constellationPlot(symbols, reference, titleText, limit)
nexttile;
n = min(numel(symbols), limit);
scatter(real(symbols(1:n)), imag(symbols(1:n)), 11, [0 0.4470 0.7410], 'filled', ...
    'MarkerFaceAlpha', 0.40); hold on;
scatter(real(reference), imag(reference), 70, [0.8500 0.3250 0.0980], 'x', 'LineWidth', 2);
axis equal; xlabel('In-phase'); ylabel('Quadrature'); prepareAxis(titleText);
end


function compareBits(original, recovered, limit)
nexttile;
n = min(numel(original), limit);
stairs(1:n, double(original(1:n)), 'Color', [0 0.4470 0.7410], 'LineWidth', 1.3); hold on;
stairs(1:n, double(recovered(1:n))+0.04, '--', 'Color', [0.8500 0.3250 0.0980], 'LineWidth', 1.0);
ylim([-0.2 1.3]); legend('Original','Recovered');
xlabel('Bit index'); ylabel('Bit'); prepareAxis('INPUT/OUTPUT · Bit comparison');
end


function errorPlot(mask, ber, bitErrors, limit)
nexttile;
n = min(numel(mask), limit);
stem(1:n, double(mask(1:n)), '.', 'Color', [0.8500 0.3250 0.0980]);
ylim([-0.1 1.2]); xlabel('Bit index'); ylabel('Error');
prepareAxis(sprintf('ERRORS · BER %.3e · %d total errors', ber, bitErrors));
end
