from database import db
from models import stats
from models.category import Category
from models.task import Task
from utils.constants import DEFAULT_COLOR
from utils.errors import NotFoundError, ValidationError
from utils.validators import require_json, validate_color


def _get_category_or_404(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


class CategoryController:
    def list_categories(self):
        task_counts = stats.count_tasks_by_category()
        return [
            {**category.to_dict(), 'task_count': task_counts.get(category.id, 0)}
            for category in Category.query.order_by(Category.id).all()
        ]

    def create_category(self, data):
        require_json(data)
        if not data.get('name'):
            raise ValidationError('Nome é obrigatório')

        category = Category(
            name=data['name'],
            description=data.get('description', ''),
            color=validate_color(data.get('color', DEFAULT_COLOR)),
        )
        db.session.add(category)
        db.session.commit()
        return category.to_dict()

    def update_category(self, category_id, data):
        category = _get_category_or_404(category_id)
        require_json(data)

        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = validate_color(data['color'])

        db.session.commit()
        return category.to_dict()

    def delete_category(self, category_id):
        category = _get_category_or_404(category_id)
        # Desassocia as tasks antes de remover a categoria, evitando referências órfãs.
        Task.query.filter_by(category_id=category_id).update({'category_id': None}, synchronize_session=False)
        db.session.delete(category)
        db.session.commit()
