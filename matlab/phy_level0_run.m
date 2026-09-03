function phy_level0_run(configPath, outputDir)
%PHY_LEVEL0_RUN Execute the complete Level 0 link and save a trace.
% All signal-processing calculations in Level 0 live in MATLAB.

cfg = jsondecode(fileread(configPath));
if ~isfolder(outputDir), mkdir(outputDir); end
rng(cfg.seed, 'twister');

switch cfg.sourceMode
    case 'Text (UTF-8)'
        sourceBytes = unicode2native(cfg.text, 'UTF-8');
        sourceBits = reshape((dec2bin(sourceBytes, 8) - '0').', 1, []);
        sourceInput = double(sourceBytes(:).');
        sourceInputLabel = 'UTF-8 bytes';
    otherwise
        sourceBits = randi([0 1], 1, cfg.numBits);
        sourceInput = 1:numel(sourceBits);
        sourceInputLabel = 'PRNG bit indices';
end

switch cfg.modulation
    case 'BPSK'
        q = 1; M = 2;
    case 'QPSK'
        q = 2; M = 4;
    case '16-QAM'
        q = 4; M = 16;
    otherwise
        error('Unsupported modulation: %s', cfg.modulation);
end

paddingCount = mod(-numel(sourceBits), q);
paddedBits = [sourceBits, zeros(1, paddingCount)]; %#ok<AGROW>
bitGroups = reshape(paddedBits, q, []).';
weights = 2.^(q-1:-1:0).';
symbolIndices = bitGroups * weights;
[labels, constellation] = localConstellation(cfg.modulation);
txSymbols = constellation(symbolIndices + 1).';

ebnoLinear = 10.^(cfg.ebnoDb/10);
n0 = 1/(q*ebnoLinear);
sigma = sqrt(n0/2);
noise = sigma*(randn(size(txSymbols)) + 1i*randn(size(txSymbols)));
rxSymbols = txSymbols + noise;

distances = abs(rxSymbols(:) - constellation(:).').^2;
[~, detectedIndices] = min(distances, [], 2);
detectedGroups = labels(detectedIndices, :);
recoveredBits = reshape(detectedGroups.', 1, []);
recoveredBits = recoveredBits(1:numel(sourceBits));
errorMask = sourceBits ~= recoveredBits;

trace = struct();
trace.config = cfg;
trace.constellation = constellation;
trace.labels = labels;
trace.sourceInput = sourceInput;
trace.sourceInputLabel = sourceInputLabel;
trace.sourceBits = sourceBits;
trace.paddedBits = paddedBits;
trace.bitGroups = bitGroups;
trace.symbolIndices = symbolIndices;
trace.txSymbols = txSymbols;
trace.noise = noise;
trace.rxSymbols = rxSymbols;
trace.detectedGroups = detectedGroups;
trace.recoveredBits = recoveredBits;
trace.errorMask = errorMask;
trace.paddingCount = paddingCount;
trace.n0 = n0;
trace.sigma = sigma;
trace.ber = sum(errorMask)/numel(sourceBits);
trace.bitErrors = sum(errorMask);
trace.numBits = numel(sourceBits);
trace.numSymbols = numel(txSymbols);

save(fullfile(outputDir, 'trace.mat'), 'trace', '-v7');
summary = struct( ...
    'ber', trace.ber, ...
    'bitErrors', trace.bitErrors, ...
    'numBits', trace.numBits, ...
    'numSymbols', trace.numSymbols, ...
    'modulation', cfg.modulation, ...
    'ebnoDb', cfg.ebnoDb, ...
    'paddingCount', paddingCount);
fid = fopen(fullfile(outputDir, 'summary.json'), 'w');
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s', jsonencode(summary));
end


function [labels, points] = localConstellation(modulation)
switch modulation
    case 'BPSK'
        labels = [0; 1];
        points = [1; -1];
    case 'QPSK'
        labels = [0 0; 0 1; 1 0; 1 1];
        i = 1 - 2*labels(:,1);
        q = 1 - 2*labels(:,2);
        points = (i + 1i*q)/sqrt(2);
    case '16-QAM'
        labels = dec2bin(0:15, 4) - '0';
        levels = [3 1 -3 -1]; % 00, 01, 10, 11: Gray order per axis
        iIndex = labels(:,1)*2 + labels(:,2) + 1;
        qIndex = labels(:,3)*2 + labels(:,4) + 1;
        points = (levels(iIndex).' + 1i*levels(qIndex).')/sqrt(10);
end
end
