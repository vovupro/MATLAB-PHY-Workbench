function phy_check_environment(outputPath)
%PHY_CHECK_ENVIRONMENT Report MATLAB and toolbox availability as JSON.
info = struct();
info.matlabVersion = version;
info.communicationsToolbox = license('test', 'communication_toolbox');
info.fiveGToolbox = license('test', '5g_toolbox');
info.signalProcessingToolbox = license('test', 'signal_toolbox');
fid = fopen(outputPath, 'w');
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s', jsonencode(info));
end
