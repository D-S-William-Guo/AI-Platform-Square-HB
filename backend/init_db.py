"""初始化数据库脚本"""
from app.database import Base, engine
from app.models import (
    App, 
    Ranking, 
    Submission, 
    SubmissionImage, 
    RankingDimension, 
    RankingLog,
    AppDimensionScore,
    HistoricalRanking
)

# 导入所有模型后，Base.metadata会包含所有表
print("Tables to create:", Base.metadata.tables.keys())

# 创建所有表
Base.metadata.create_all(bind=engine)
print("Database initialized successfully!")
