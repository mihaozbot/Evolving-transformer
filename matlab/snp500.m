
name_data = '..\data\snp500_data.csv';
name_dates = '..\data\snp500_dates.csv';
data = readtable(name_data);
dates = readtable(name_dates,'ReadVariableNames',true);
%data(:, 1) = datetime(data(:, 1), 'InputFormat', 'yyyy-MM-dd');
dates = table2array(dates(:,1));
%data = table(:,2);

candle(data)

