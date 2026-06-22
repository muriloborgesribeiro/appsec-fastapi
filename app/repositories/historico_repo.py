from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import DiagnosisHistory


class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, dados: dict, resultados: dict) -> DiagnosisHistory:
        alvarado = resultados["alvarado"]
        knn = resultados["knn"]
        svm = resultados["svm"]
        knn_ok = "erro" not in knn
        svm_ok = "erro" not in svm

        historico = DiagnosisHistory(
            dor_migratoria=bool(dados.get("dor_migratoria")),
            anorexia=bool(dados.get("anorexia")),
            nauseas_vomitos=bool(dados.get("nauseas_vomitos")),
            dor_fid=bool(dados.get("dor_fid")),
            descompressao_dolorosa=bool(dados.get("descompressao_dolorosa")),
            temperatura=float(dados.get("temperatura", 36.5)),
            leucocitos=int(dados.get("leucocitos", 8000)),
            neutrofilia=bool(dados.get("neutrofilia")),
            alvarado_score=alvarado.get("score"),
            alvarado_classificacao=alvarado.get("classificacao"),
            predicao_knn=knn.get("classe_predita") if knn_ok else None,
            probabilidade_knn=knn.get("probabilidade_apendicite") if knn_ok else None,
            confianca_knn=knn.get("confianca", "") if knn_ok else "",
            predicao_svm=svm.get("classe_predita") if svm_ok else None,
            probabilidade_svm=svm.get("probabilidade_apendicite") if svm_ok else None,
            confianca_svm=svm.get("confianca", "") if svm_ok else "",
        )
        self.db.add(historico)
        self.db.commit()
        self.db.refresh(historico)
        return historico

    def find_by_id(self, diagnostico_id: int) -> Optional[DiagnosisHistory]:
        return (
            self.db.query(DiagnosisHistory)
            .filter(DiagnosisHistory.id == diagnostico_id)
            .first()
        )

    def find_by_id_or_404(self, diagnostico_id: int) -> DiagnosisHistory:
        historico = self.find_by_id(diagnostico_id)
        if not historico:
            raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")
        return historico

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        classificacao: Optional[str] = None,
        resultado_knn: Optional[str] = None,
        resultado_svm: Optional[str] = None,
    ):
        query = self.db.query(DiagnosisHistory)

        if data_inicio:
            query = query.filter(DiagnosisHistory.created_at >= data_inicio)
        if data_fim:
            fim = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(DiagnosisHistory.created_at < fim)
        if classificacao:
            query = query.filter(
                DiagnosisHistory.alvarado_classificacao == classificacao
            )
        if resultado_knn:
            query = query.filter(
                DiagnosisHistory.predicao_knn == int(resultado_knn)
            )
        if resultado_svm:
            query = query.filter(
                DiagnosisHistory.predicao_svm == int(resultado_svm)
            )

        total = query.count()
        offset = (page - 1) * page_size
        registros = (
            query.order_by(DiagnosisHistory.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return registros, total

    def delete(self, diagnostico_id: int):
        historico = self.find_by_id_or_404(diagnostico_id)
        self.db.delete(historico)
        self.db.commit()
