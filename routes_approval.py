from flask import Blueprint, request, redirect, url_for
from models import db, ApprovalStep, DocumentInstance
from auth import login_required, get_current_user
from datetime import datetime

approval_bp = Blueprint('approval', __name__, url_prefix='/approval')

@approval_bp.route('/')
@login_required
def approval_list():
    user = get_current_user()
    # Находим все шаги, где approver_id = текущий пользователь и решение ещё не принято
    steps = ApprovalStep.query.filter_by(approver_id=user.id).filter(ApprovalStep.decision.is_(None)).all()
    html = '<h2>Документы на согласование</h2>'
    if not steps:
        html += '<p>Нет документов, ожидающих вашего решения.</p>'
    else:
        html += '<ul>'
        for step in steps:
            doc = step.document
            html += f'<li><a href="/approval/{step.id}">{doc.document_type.name} от {doc.creator.username} ({doc.created_at.strftime("%d.%m.%Y %H:%M")})</a></li>'
        html += '</ul>'
    html += '<p><a href="/">🔙 На главную</a></p>'
    return html

@approval_bp.route('/<int:step_id>', methods=['GET', 'POST'])
@login_required
def handle_approval(step_id):
    step = ApprovalStep.query.get_or_404(step_id)
    if step.approver_id != get_current_user().id:
        return 'Доступ запрещён.', 403
    if step.decision is not None:
        return 'Вы уже приняли решение по этому документу.', 400

    doc = step.document
    if request.method == 'POST':
        decision = request.form.get('decision')
        comment = request.form.get('comment', '')
        if decision not in ['approved', 'rejected']:
            return 'Неверное решение.', 400
        step.decision = decision
        step.comment = comment
        step.decided_at = datetime.utcnow()
        db.session.commit()
        # Если все подписанты приняли решение, можно изменить общий статус (упростим: если все approved -> approved, если хоть один rejected -> rejected)
        all_steps = ApprovalStep.query.filter_by(document_id=doc.id).all()
        if all(step.decision == 'approved' for step in all_steps):
            doc.status = 'approved'
        elif any(step.decision == 'rejected' for step in all_steps):
            doc.status = 'rejected'
        db.session.commit()
        return redirect(url_for('approval.approval_list'))

    # Показ информации о документе и форма решения
    html = f'<h2>Согласование: {doc.document_type.name}</h2>'
    html += f'<p>Создатель: {doc.creator.username} | Создан: {doc.created_at.strftime("%d.%m.%Y %H:%M")}</p>'
    # Покажем поля документа (сокращённо)
    html += '<table border="1" cellpadding="5"><tr><th>Поле</th><th>Значение</th></tr>'
    for fv in doc.field_values:
        html += f'<tr><td>{fv.field.field_name}</td><td>{fv.value}</td></tr>'
    html += '</table>'

    html += '''
        <h3>Ваше решение</h3>
        <form method="post">
            <label><input type="radio" name="decision" value="approved" required> Подписать</label><br>
            <label><input type="radio" name="decision" value="rejected"> Отклонить</label><br><br>
            <label>Комментарий:<br><textarea name="comment"></textarea></label><br><br>
            <button type="submit">Отправить решение</button>
        </form>
    '''
    html += '<p><a href="/approval">🔙 Назад к списку</a></p>'
    return html
