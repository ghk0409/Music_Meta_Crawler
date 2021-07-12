import os

# DataFrame to CSV (csv 파일 만들고 이어쓰기 하기)
def result2csv(result_path, df):
    if not os.path.exists(result_path):
        df.to_csv(result_path, mode='w', encoding='utf-8-sig', index=False)
    else:
        df.to_csv(result_path, mode='a', header=False, encoding='utf-8-sig', index=False)