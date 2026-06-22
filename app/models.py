from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class DiagnosisHistory(Base):
    __tablename__ = "diagnostico_avaliacao"

    id = Column(Integer, primary_key=True, index=True)
    dor_migratoria = Column("dor_migratoria", Boolean, nullable=False)
    anorexia = Column("anorexia", Boolean, nullable=False)
    nauseas_vomitos = Column("nauseas_vomitos", Boolean, nullable=False)
    dor_fid = Column("dor_fid", Boolean, nullable=False)
    descompressao_dolorosa = Column("descompressao_dolorosa", Boolean, nullable=False)
    temperatura = Column("temperatura", Float, nullable=False)
    leucocitos = Column("leucocitos", Integer, nullable=False)
    neutrofilia = Column("neutrofilia", Boolean, nullable=False)
    alvarado_score = Column("score_alvarado", Integer, nullable=False)
    alvarado_classificacao = Column("classificacao_alvarado", String(20), nullable=False)
    predicao_knn = Column("predicao_knn", Integer, nullable=True)
    probabilidade_knn = Column("probabilidade_knn", Float, nullable=True)
    confianca_knn = Column("confianca_knn", String(20), nullable=False)
    created_at = Column("criado_em", DateTime, default=func.now(), nullable=False)
    predicao_svm = Column("predicao_svm", Integer, nullable=True)
    probabilidade_svm = Column("probabilidade_svm", Float, nullable=True)
    confianca_svm = Column("confianca_svm", String(50), nullable=False)
