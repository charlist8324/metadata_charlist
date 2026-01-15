from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import DataSource, TableMetadata, ColumnMetadata, ExtractionHistory, TableRelationship, ETLTask
from db_manager import get_db_session
from extractor_base import (
    MySQLMetadataExtractor, 
    PostgreSQLMetadataExtractor, 
    SQLServerMetadataExtractor, 
    OracleMetadataExtractor
)
from datetime import datetime
from auth import login_required, admin_required, login_user, logout_user, get_current_user, has_permission, init_auth_tables, create_user, update_user, delete_user, get_all_users, get_user_by_id, change_user_password
import json
import os
from exceptions import DataSourceNotFoundException, ExtractionException, ValidationException, DatabaseConnectionException
import logging


def create_app():
    app = Flask(__name__)
    
    # 设置SECRET_KEY，用于session加密
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this-in-production')
    
    # 初始化数据库管理器
    from db_manager import init_db_manager
    from config import Config
    init_db_manager(Config.DATABASE_URL)
    
    # 数据库类型到抽取器的映射
    EXTRACTOR_MAP = {
        'mysql': MySQLMetadataExtractor,
        'postgresql': PostgreSQLMetadataExtractor,
        'sqlserver': SQLServerMetadataExtractor,
        'oracle': OracleMetadataExtractor
    }
    
    @app.route('/api/data-sources', methods=['GET'])
    @login_required
    def get_data_sources():
        """获取所有数据源"""
        try:
            with get_db_session() as session:
                sources = session.query(DataSource).all()
                return jsonify([{
                    'id': source.id,
                    'name': source.name,
                    'type': source.type,
                    'host': source.host,
                    'port': source.port,
                    'database': source.database,
                    'created_at': source.created_at.isoformat() if source.created_at else None,
                    'updated_at': source.updated_at.isoformat() if source.updated_at else None
                } for source in sources])
        except Exception as e:
            logging.error(f"获取数据源失败: {str(e)}")
            return jsonify({'error': f'获取数据源失败: {str(e)}'}), 500
    
    @app.route('/api/data-sources', methods=['POST'])
    @login_required
    def create_data_source():
        """创建新的数据源"""
        try:
            data = request.json
            
            # 验证必需字段
            required_fields = ['name', 'type', 'host', 'port', 'username', 'password', 'database']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'缺少必需字段: {field}'}), 400
            
            # 验证数据库类型
            if data['type'] not in EXTRACTOR_MAP:
                return jsonify({'error': f'不支持的数据库类型: {data["type"]}'}), 400
            
            with get_db_session() as session:
                # 检查数据源名称是否已存在
                existing = session.query(DataSource).filter(DataSource.name == data['name']).first()
                if existing:
                    return jsonify({'error': '数据源名称已存在'}), 400
                
                # 创建新的数据源
                new_source = DataSource(
                    name=data['name'],
                    type=data['type'],
                    host=data['host'],
                    port=data['port'],
                    username=data['username'],
                    password=data['password'],
                    database=data['database']
                )
                
                session.add(new_source)
                session.flush()  # 获取新插入记录的ID
                
                return jsonify({
                    'id': new_source.id,
                    'name': new_source.name,
                    'type': new_source.type,
                    'host': new_source.host,
                    'port': new_source.port,
                    'database': new_source.database
                }), 201
        except ValidationException as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logging.error(f"创建数据源失败: {str(e)}")
            return jsonify({'error': f'创建数据源失败: {str(e)}'}), 500
    
    @app.route('/api/data-sources/<int:source_id>', methods=['GET'])
    @login_required
    def get_data_source(source_id):
        """获取单个数据源信息"""
        try:
            with get_db_session() as session:
                source = session.query(DataSource).filter(DataSource.id == source_id).first()
                if not source:
                    return jsonify({'error': '数据源不存在'}), 404
                
                return jsonify({
                    'id': source.id,
                    'name': source.name,
                    'type': source.type,
                    'host': source.host,
                    'port': source.port,
                    'database': source.database,
                    'created_at': source.created_at.isoformat() if source.created_at else None,
                    'updated_at': source.updated_at.isoformat() if source.updated_at else None
                })
        except Exception as e:
            logging.error(f"获取数据源失败: {str(e)}")
            return jsonify({'error': f'获取数据源失败: {str(e)}'}), 500
    
    @app.route('/api/data-sources/<int:source_id>', methods=['PUT'])
    @login_required
    def update_data_source(source_id):
        """更新数据源信息"""
        try:
            data = request.json
            
            with get_db_session() as session:
                source = session.query(DataSource).filter(DataSource.id == source_id).first()
                if not source:
                    return jsonify({'error': '数据源不存在'}), 404
                
                # 更新允许修改的字段
                updatable_fields = ['name', 'type', 'host', 'port', 'username', 'password', 'database']
                for field in updatable_fields:
                    if field in data:
                        setattr(source, field, data[field])
                
                return jsonify({
                    'id': source.id,
                    'name': source.name,
                    'type': source.type,
                    'host': source.host,
                    'port': source.port,
                    'database': source.database
                })
        except Exception as e:
            logging.error(f"更新数据源失败: {str(e)}")
            return jsonify({'error': f'更新数据源失败: {str(e)}'}), 500
    
    @app.route('/api/data-sources/<int:source_id>', methods=['DELETE'])
    @login_required
    def delete_data_source(source_id):
        """删除数据源"""
        try:
            with get_db_session() as session:
                source = session.query(DataSource).filter(DataSource.id == source_id).first()
                if not source:
                    return jsonify({'error': '数据源不存在'}), 404
                
                session.delete(source)
                return jsonify({'message': '数据源删除成功'})
        except Exception as e:
            logging.error(f"删除数据源失败: {str(e)}")
            return jsonify({'error': f'删除数据源失败: {str(e)}'}), 500
    
    @app.route('/api/data-sources/<int:source_id>/test', methods=['GET'])
    @login_required
    def test_connection(source_id):
        """测试数据源连接"""
        try:
            with get_db_session() as session:
                source = session.query(DataSource).filter(DataSource.id == source_id).first()
                if not source:
                    return jsonify({'success': False, 'error': '数据源不存在'}), 404
                
                # 根据数据库类型选择对应的抽取器
                extractor_class = EXTRACTOR_MAP.get(source.type)
                if not extractor_class:
                    return jsonify({'success': False, 'error': f'不支持的数据库类型: {source.type}'}), 400
                
                extractor = extractor_class(source)
                try:
                    success = extractor.connect()
                    if success:
                        extractor.disconnect()  # 断开连接
                        return jsonify({'success': True, 'message': '连接测试成功'})
                    else:
                        return jsonify({'success': False, 'error': '连接失败'})
                except Exception as e:
                    logging.error(f"测试连接失败: {str(e)}")
                    return jsonify({'success': False, 'error': str(e)})
        except DataSourceNotFoundException as e:
            return jsonify({'success': False, 'error': str(e)}), 404
        except DatabaseConnectionException as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        except Exception as e:
            logging.error(f"测试连接失败: {str(e)}")
            return jsonify({'success': False, 'error': f'连接测试失败: {str(e)}'}), 500
    
    @app.route('/api/data-sources/<int:source_id>/extract', methods=['POST'])
    @login_required
    def extract_metadata(source_id):
        """抽取指定数据源的元数据"""
        try:
            with get_db_session() as session:
                source = session.query(DataSource).filter(DataSource.id == source_id).first()
                if not source:
                    return jsonify({'error': '数据源不存在'}), 404
                
                # 根据数据库类型选择对应的抽取器
                if source.type not in EXTRACTOR_MAP:
                    return jsonify({'error': f'不支持的数据库类型: {source.type}'}), 400
                
                extractor_class = EXTRACTOR_MAP[source.type]
                extractor = extractor_class(source)
                
                # 执行元数据抽取
                result = extractor.extract_all_metadata()
                
                # 记录抽取历史
                history_record = ExtractionHistory(
                    datasource_id=source.id,
                    status=result['status'],
                    message=result.get('message', ''),
                    extracted_tables=result.get('tables_count', 0)
                )
                session.add(history_record)
                
                if result['status'] == 'success':
                    # 清除旧的元数据（保留历史数据，但清空关联的表和列数据）
                    # 获取该数据源下的所有表
                    existing_tables = session.query(TableMetadata).filter(
                        TableMetadata.datasource_id == source.id
                    ).all()
                    
                    # 删除所有关联的列、表和关系数据
                    for table in existing_tables:
                        # 删除关联的列
                        session.query(ColumnMetadata).filter(
                            ColumnMetadata.table_id == table.id
                        ).delete()
                        
                        # 删除关联的关系
                        session.query(TableRelationship).filter(
                            TableRelationship.table_id == table.id
                        ).delete()
                        session.query(TableRelationship).filter(
                            TableRelationship.referenced_table_id == table.id
                        ).delete()
                    
                    # 删除表本身
                    session.query(TableMetadata).filter(
                        TableMetadata.datasource_id == source.id
                    ).delete()
                    
                    # 创建新的元数据
                    # 首先创建所有表并建立表名到ID的映射
                    table_mapping = {}
                    for table_data in result['tables']:
                        table_info = table_data['table_info']
                        
                        # 创建新表记录
                        table_meta = TableMetadata(
                            table_name=table_info['table_name'],
                            schema_name=table_info['schema_name'],
                            row_count=table_info['row_count'],
                            size_bytes=table_info['size_bytes'],
                            comment=table_info['comment'],
                            datasource_id=source.id
                        )
                        session.add(table_meta)
                        session.flush()  # 获取自动生成的ID
                        
                        # 存储表名到ID的映射
                        table_mapping[f"{table_info['schema_name']}.{table_info['table_name']}"] = table_meta.id
                        
                        # 处理列元数据
                        for col_data in table_data['columns']:
                            column_meta = ColumnMetadata(
                                column_name=col_data['column_name'],
                                data_type=col_data['data_type'],
                                is_nullable=col_data['is_nullable'],
                                default_value=col_data['default_value'],
                                column_comment=col_data['column_comment'],
                                ordinal_position=col_data['ordinal_position'],
                                table_id=table_meta.id
                            )
                            session.add(column_meta)
                    
                    # 创建关联关系
                    for relationship in result.get('relationships', []):
                        # 根据不同数据库类型调整键的格式
                        if source.type == 'mysql':
                            table_name_key = f"{source.database}.{relationship['table_name']}"
                            referenced_table_name_key = f"{source.database}.{relationship['referenced_table_name']}"
                        elif source.type == 'postgresql':
                            table_name_key = f"public.{relationship['table_name']}"  # PostgreSQL通常使用public schema
                            referenced_table_name_key = f"public.{relationship['referenced_table_name']}"
                        elif source.type == 'sqlserver':
                            table_name_key = f"dbo.{relationship['table_name']}"  # SQL Server通常使用dbo schema
                            referenced_table_name_key = f"dbo.{relationship['referenced_table_name']}"
                        elif source.type == 'oracle':
                            table_name_key = f"{source.username.upper()}.{relationship['table_name']}"  # Oracle schema通常是用户名
                            referenced_table_name_key = f"{source.username.upper()}.{relationship['referenced_table_name']}"
                        else:
                            table_name_key = f"{source.database}.{relationship['table_name']}"
                            referenced_table_name_key = f"{source.database}.{relationship['referenced_table_name']}"
                        
                        table_id = table_mapping.get(table_name_key)
                        referenced_table_id = table_mapping.get(referenced_table_name_key)
                        
                        if table_id and referenced_table_id:
                            rel = TableRelationship(
                                constraint_name=relationship.get('constraint_name'),
                                table_id=table_id,
                                referenced_table_id=referenced_table_id,
                                column_name=relationship['column_name'],
                                referenced_column_name=relationship['referenced_column_name'],
                                constraint_type=relationship.get('constraint_type', 'FOREIGN KEY')
                            )
                            session.add(rel)
                
                session.commit()
                
                return jsonify(result)
        except DataSourceNotFoundException as e:
            return jsonify({'error': str(e)}), 404
        except ExtractionException as e:
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            # 捕获所有异常并返回JSON格式错误
            logging.error(f"元数据抽取失败: {str(e)}")
            return jsonify({'error': f'元数据抽取失败: {str(e)}'}), 500
    
    @app.route('/api/etl-tasks', methods=['GET'])
    @login_required
    def get_etl_tasks():
        """获取ETL任务列表"""
        try:
            with get_db_session() as session:
                tasks = session.query(ETLTask).all()
                return jsonify([{
                    'id': task.id,
                    'name': task.name,
                    'task_type': task.task_type,
                    'datasource_id': task.datasource_id,
                    'datasource_name': task.datasource.name if task.datasource else 'Unknown',
                    'schedule_type': task.schedule_type,
                    'interval_value': task.interval_value,
                    'interval_unit': task.interval_unit,
                    'cron_expression': task.cron_expression,
                    'status': task.status,
                    'description': task.description,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'created_at': task.created_at.isoformat() if task.created_at else None
                } for task in tasks])
        except Exception as e:
            logging.error(f"获取ETL任务失败: {str(e)}")
            return jsonify({'error': f'获取ETL任务失败: {str(e)}'}), 500
    
    @app.route('/api/etl-tasks/<int:task_id>', methods=['GET'])
    @login_required
    def get_etl_task(task_id):
        """获取单个ETL任务"""
        try:
            with get_db_session() as session:
                task = session.query(ETLTask).filter(ETLTask.id == task_id).first()
                if not task:
                    return jsonify({'error': 'ETL任务不存在'}), 404
                
                return jsonify({
                    'id': task.id,
                    'name': task.name,
                    'task_type': task.task_type,
                    'datasource_id': task.datasource_id,
                    'datasource_name': task.datasource.name if task.datasource else 'Unknown',
                    'schedule_type': task.schedule_type,
                    'interval_value': task.interval_value,
                    'interval_unit': task.interval_unit,
                    'cron_expression': task.cron_expression,
                    'status': task.status,
                    'description': task.description,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None
                })
        except Exception as e:
            logging.error(f"获取ETL任务失败: {str(e)}")
            return jsonify({'error': f'获取ETL任务失败: {str(e)}'}), 500
    
    @app.route('/api/etl-tasks', methods=['POST'])
    @login_required
    def create_etl_task():
        """创建ETL任务"""
        try:
            data = request.json
            
            # 验证必需字段
            required_fields = ['name', 'task_type', 'datasource_id', 'schedule_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'缺少必需字段: {field}'}), 400
            
            with get_db_session() as session:
                # 验证数据源是否存在
                source = session.query(DataSource).filter(DataSource.id == data['datasource_id']).first()
                if not source:
                    return jsonify({'error': '数据源不存在'}), 400
                
                # 创建ETL任务
                new_task = ETLTask(
                    name=data['name'],
                    task_type=data['task_type'],
                    datasource_id=data['datasource_id'],
                    schedule_type=data['schedule_type'],
                    interval_value=data.get('interval_value'),
                    interval_unit=data.get('interval_unit'),
                    cron_expression=data.get('cron_expression'),
                    status=data.get('status', 'active'),
                    description=data.get('description')
                )
                
                session.add(new_task)
                session.flush()
                
                return jsonify({
                    'id': new_task.id,
                    'name': new_task.name,
                    'message': 'ETL任务创建成功'
                }), 201
        except ValidationException as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logging.error(f"创建ETL任务失败: {str(e)}")
            return jsonify({'error': f'创建ETL任务失败: {str(e)}'}), 500
    
    @app.route('/api/etl-tasks/<int:task_id>', methods=['PUT'])
    @login_required
    def update_etl_task(task_id):
        """更新ETL任务"""
        try:
            data = request.json
            
            with get_db_session() as session:
                task = session.query(ETLTask).filter(ETLTask.id == task_id).first()
                if not task:
                    return jsonify({'error': 'ETL任务不存在'}), 404
                
                # 更新字段
                updatable_fields = ['name', 'task_type', 'datasource_id', 'schedule_type', 
                                   'interval_value', 'interval_unit', 'cron_expression', 
                                   'status', 'description']
                for field in updatable_fields:
                    if field in data:
                        setattr(task, field, data[field])
                
                return jsonify({
                    'id': task.id,
                    'message': 'ETL任务更新成功'
                })
        except Exception as e:
            logging.error(f"更新ETL任务失败: {str(e)}")
            return jsonify({'error': f'更新ETL任务失败: {str(e)}'}), 500
    
    @app.route('/api/etl-tasks/<int:task_id>', methods=['DELETE'])
    @login_required
    def delete_etl_task(task_id):
        """删除ETL任务"""
        try:
            with get_db_session() as session:
                task = session.query(ETLTask).filter(ETLTask.id == task_id).first()
                if not task:
                    return jsonify({'error': 'ETL任务不存在'}), 404
                
                session.delete(task)
                return jsonify({'message': 'ETL任务删除成功'})
        except Exception as e:
            logging.error(f"删除ETL任务失败: {str(e)}")
            return jsonify({'error': f'删除ETL任务失败: {str(e)}'}), 500
    
    @app.route('/api/etl-tasks/<int:task_id>/execute', methods=['POST'])
    @login_required
    def execute_etl_task(task_id):
        """执行ETL任务 - 进行元数据抽取"""
        try:
            with get_db_session() as session:
                task = session.query(ETLTask).filter(ETLTask.id == task_id).first()
                if not task:
                    return jsonify({'error': 'ETL任务不存在'}), 404

                # 获取关联的数据源
                source = session.query(DataSource).filter(DataSource.id == task.datasource_id).first()
                if not source:
                    return jsonify({'error': '数据源不存在'}), 404

                # 根据数据库类型选择对应的抽取器
                if source.type not in EXTRACTOR_MAP:
                    return jsonify({'error': f'不支持的数据库类型: {source.type}'}), 400

                extractor_class = EXTRACTOR_MAP[source.type]
                extractor = extractor_class(source)

                # 根据任务类型选择抽取方法
                task_type = task.task_type

                if task_type == 'full':
                    # 全量抽取
                    result = extractor.extract_all_metadata()
                    full_extraction = True
                elif task_type == 'incremental':
                    # 增量抽取：获取上次执行时间
                    last_history = session.query(ExtractionHistory).filter(
                        ExtractionHistory.etl_task_id == task_id
                    ).order_by(ExtractionHistory.extraction_time.desc()).first()

                    last_sync_time = last_history.extraction_time if last_history else None
                    result = extractor.extract_incremental_metadata(last_sync_time)
                    full_extraction = False
                elif task_type == 'schema_only':
                    # 仅结构抽取
                    result = extractor.extract_schema_only_metadata()
                    full_extraction = True
                else:
                    return jsonify({'error': f'不支持的任务类型: {task_type}'}), 400

                # 更新任务执行时间
                task.last_run = datetime.utcnow()

                # 记录抽取历史
                history_record = ExtractionHistory(
                    datasource_id=source.id,
                    status=result['status'],
                    message=result.get('message', ''),
                    extracted_tables=result.get('tables_count', 0),
                    etl_task_id=task.id
                )
                session.add(history_record)

                if result['status'] == 'success':
                    if full_extraction:
                        # 全量抽取和仅结构抽取：清除旧数据
                        existing_tables = session.query(TableMetadata).filter(
                            TableMetadata.datasource_id == source.id
                        ).all()

                        for table in existing_tables:
                            session.query(ColumnMetadata).filter(
                                ColumnMetadata.table_id == table.id
                            ).delete()
                            session.query(TableRelationship).filter(
                                TableRelationship.table_id == table.id
                            ).delete()
                            session.query(TableRelationship).filter(
                                TableRelationship.referenced_table_id == table.id
                            ).delete()

                        session.query(TableMetadata).filter(
                            TableMetadata.datasource_id == source.id
                        ).delete()
                    # 增量抽取不清除旧数据

                    # 创建/更新新的元数据
                    table_mapping = {}
                    for table_data in result['tables']:
                        table_info = table_data['table_info']
                        table_key = f"{table_info['schema_name']}.{table_info['table_name']}"

                        # 增量抽取：检查表是否已存在
                        existing_table = None
                        if not full_extraction:
                            existing_table = session.query(TableMetadata).filter(
                                TableMetadata.datasource_id == source.id,
                                TableMetadata.table_name == table_info['table_name'],
                                TableMetadata.schema_name == table_info['schema_name']
                            ).first()

                        if existing_table:
                            # 更新现有表
                            existing_table.row_count = table_info['row_count']
                            existing_table.size_bytes = table_info['size_bytes']
                            existing_table.comment = table_info['comment']
                            existing_table.updated_at = datetime.utcnow()
                            table_meta = existing_table

                            # 删除旧字段
                            session.query(ColumnMetadata).filter(
                                ColumnMetadata.table_id == existing_table.id
                            ).delete()
                        else:
                            # 创建新表
                            table_meta = TableMetadata(
                                table_name=table_info['table_name'],
                                schema_name=table_info['schema_name'],
                                row_count=table_info['row_count'],
                                size_bytes=table_info['size_bytes'],
                                comment=table_info['comment'],
                                datasource_id=source.id
                            )
                            session.add(table_meta)
                            session.flush()

                        table_mapping[table_key] = table_meta.id

                        # 添加/更新字段
                        for col_data in table_data['columns']:
                            column_meta = ColumnMetadata(
                                column_name=col_data['column_name'],
                                data_type=col_data['data_type'],
                                is_nullable=col_data['is_nullable'],
                                default_value=col_data['default_value'],
                                column_comment=col_data['column_comment'],
                                ordinal_position=col_data['ordinal_position'],
                                table_id=table_meta.id
                            )
                            session.add(column_meta)

                    # 只有全量抽取才创建关联关系
                    if full_extraction and 'relationships' in result:
                        for relationship in result.get('relationships', []):
                            if source.type == 'mysql':
                                table_name_key = f"{source.database}.{relationship['table_name']}"
                                referenced_table_name_key = f"{source.database}.{relationship['referenced_table_name']}"
                            elif source.type == 'postgresql':
                                table_name_key = f"public.{relationship['table_name']}"
                                referenced_table_name_key = f"public.{relationship['referenced_table_name']}"
                            elif source.type == 'sqlserver':
                                table_name_key = f"dbo.{relationship['table_name']}"
                                referenced_table_name_key = f"dbo.{relationship['referenced_table_name']}"
                            elif source.type == 'oracle':
                                table_name_key = f"{source.username.upper()}.{relationship['table_name']}"
                                referenced_table_name_key = f"{source.username.upper()}.{relationship['referenced_table_name']}"
                            else:
                                table_name_key = f"{source.database}.{relationship['table_name']}"
                                referenced_table_name_key = f"{source.database}.{relationship['referenced_table_name']}"

                            table_id = table_mapping.get(table_name_key)
                            referenced_table_id = table_mapping.get(referenced_table_name_key)

                            if table_id and referenced_table_id:
                                rel = TableRelationship(
                                    constraint_name=relationship.get('constraint_name'),
                                    table_id=table_id,
                                    referenced_table_id=referenced_table_id,
                                    column_name=relationship['column_name'],
                                    referenced_column_name=relationship['referenced_column_name'],
                                    constraint_type=relationship.get('constraint_type', 'FOREIGN KEY')
                                )
                                session.add(rel)

                session.commit()

                return jsonify({
                    'success': result['status'] == 'success',
                    'status': result['status'],
                    'message': result.get('message', ''),
                    'tables_count': result.get('tables_count', 0),
                    'extraction_type': result.get('extraction_type', 'full')
                })
        except Exception as e:
            logging.error(f"执行ETL任务失败: {str(e)}")
            return jsonify({'error': f'执行ETL任务失败: {str(e)}'}), 500
    
    @app.route('/api/data-sources/<int:source_id>/tables', methods=['GET'])
    @login_required
    def get_tables(source_id):
        """获取指定数据源的所有表"""
        try:
            with get_db_session() as session:
                # 验证数据源是否存在
                source = session.query(DataSource).filter(DataSource.id == source_id).first()
                if not source:
                    return jsonify({'error': '数据源不存在'}), 404
                
                # 查询该数据源下的所有表
                tables = session.query(TableMetadata).filter(
                    TableMetadata.datasource_id == source_id
                ).all()
                
                return jsonify([{
                    'id': table.id,
                    'table_name': table.table_name,
                    'schema_name': table.schema_name,
                    'row_count': table.row_count,
                    'size_bytes': table.size_bytes,
                    'comment': table.comment,
                    'created_at': table.created_at.isoformat() if table.created_at else None,
                    'updated_at': table.updated_at.isoformat() if table.updated_at else None
                } for table in tables])
        except Exception as e:
            logging.error(f"获取表列表失败: {str(e)}")
            return jsonify({'error': f'获取表列表失败: {str(e)}'}), 500
    
    @app.route('/api/tables/<int:table_id>', methods=['GET'])
    @login_required
    def get_table(table_id):
        """获取指定表的详细信息，包括关联关系"""
        try:
            with get_db_session() as session:
                # 验证表是否存在
                table = session.query(TableMetadata).filter(TableMetadata.id == table_id).first()
                if not table:
                    return jsonify({'error': '表不存在'}), 404
                
                # 获取表的所有列
                columns = session.query(ColumnMetadata).filter(
                    ColumnMetadata.table_id == table_id
                ).order_by(ColumnMetadata.ordinal_position).all()
                
                # 获取该表的关联关系
                relationships = session.query(TableRelationship).filter(
                    (TableRelationship.table_id == table_id) | 
                    (TableRelationship.referenced_table_id == table_id)
                ).all()
                
                # 获取关联的表信息
                related_tables = []
                for rel in relationships:
                    if rel.table_id == table_id:
                        # 当前表是主表
                        referenced_table = session.query(TableMetadata).filter(
                            TableMetadata.id == rel.referenced_table_id
                        ).first()
                        related_tables.append({
                            'type': 'outgoing',  # 从当前表指向其他表
                            'constraint_name': rel.constraint_name,
                            'column_name': rel.column_name,
                            'referenced_table_name': referenced_table.table_name if referenced_table else 'Unknown',
                            'referenced_column_name': rel.referenced_column_name,
                            'constraint_type': rel.constraint_type
                        })
                    else:
                        # 当前表是被引用表
                        referencing_table = session.query(TableMetadata).filter(
                            TableMetadata.id == rel.table_id
                        ).first()
                        related_tables.append({
                            'type': 'incoming',  # 从其他表指向当前表
                            'constraint_name': rel.constraint_name,
                            'column_name': rel.column_name,
                            'referencing_table_name': referencing_table.table_name if referencing_table else 'Unknown',
                            'referencing_column_name': rel.column_name,
                            'constraint_type': rel.constraint_type
                        })
                
                return jsonify({
                    'id': table.id,
                    'table_name': table.table_name,
                    'schema_name': table.schema_name,
                    'row_count': table.row_count,
                    'size_bytes': table.size_bytes,
                    'comment': table.comment,
                    'created_at': table.created_at.isoformat() if table.created_at else None,
                    'updated_at': table.updated_at.isoformat() if table.updated_at else None,
                    'columns': [{
                        'id': col.id,
                        'column_name': col.column_name,
                        'data_type': col.data_type,
                        'is_nullable': col.is_nullable,
                        'default_value': col.default_value,
                        'column_comment': col.column_comment,
                        'ordinal_position': col.ordinal_position,
                        'created_at': col.created_at.isoformat() if col.created_at else None,
                        'updated_at': col.updated_at.isoformat() if col.updated_at else None
                    } for col in columns],
                    'relationships': related_tables
                })
        except Exception as e:
            logging.error(f"获取表详情失败: {str(e)}")
            return jsonify({'error': f'获取表详情失败: {str(e)}'}), 500
    
    @app.route('/api/tables/<int:table_id>/columns', methods=['GET'])
    @login_required
    def get_columns(table_id):
        """获取指定表的所有列"""
        try:
            with get_db_session() as session:
                # 验证表是否存在
                table = session.query(TableMetadata).filter(TableMetadata.id == table_id).first()
                if not table:
                    return jsonify({'error': '表不存在'}), 404
                
                # 查询该表的所有列
                columns = session.query(ColumnMetadata).filter(
                    ColumnMetadata.table_id == table_id
                ).order_by(ColumnMetadata.ordinal_position).all()
                
                return jsonify([{
                    'id': col.id,
                    'column_name': col.column_name,
                    'data_type': col.data_type,
                    'is_nullable': col.is_nullable,
                    'default_value': col.default_value,
                    'column_comment': col.column_comment,
                    'ordinal_position': col.ordinal_position,
                    'created_at': col.created_at.isoformat() if col.created_at else None,
                    'updated_at': col.updated_at.isoformat() if col.updated_at else None
                } for col in columns])
        except Exception as e:
            logging.error(f"获取列信息失败: {str(e)}")
            return jsonify({'error': f'获取列信息失败: {str(e)}'}), 500
    
    @app.route('/api/extraction-history', methods=['GET'])
    @login_required
    def get_extraction_history():
        """获取元数据抽取历史"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            with get_db_session() as session:
                history_records = session.query(ExtractionHistory).order_by(
                    ExtractionHistory.extraction_time.desc()
                ).offset((page - 1) * per_page).limit(per_page).all()
                
                total = session.query(ExtractionHistory).count()
                
                return jsonify({
                    'history': [{
                        'id': record.id,
                        'datasource_id': record.datasource_id,
                        'datasource_name': record.datasource.name if record.datasource else 'Unknown',
                        'extraction_time': record.extraction_time.isoformat() if record.extraction_time else None,
                        'status': record.status,
                        'message': record.message,
                        'extracted_tables': record.extracted_tables
                    } for record in history_records],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total + per_page - 1) // per_page
                    }
                })
        except Exception as e:
            logging.error(f"获取抽取历史失败: {str(e)}")
            return jsonify({'error': f'获取抽取历史失败: {str(e)}'}), 500
    
    @app.route('/api/overview')
    @login_required
    def get_overview():
        """获取资源概览数据"""
        try:
            with get_db_session() as session:
                # 获取数据源数量
                data_sources_count = session.query(DataSource).count()
                
                # 获取表数量
                tables_count = session.query(TableMetadata).count()
                
                # 获取字段数量
                columns_count = session.query(ColumnMetadata).count()
                
                # 获取总数据量
                total_size = session.query(ExtractionHistory).with_entities(
                    func.sum(ExtractionHistory.extracted_tables)
                ).scalar() or 0
                
                # 获取最近抽取记录
                recent_extraction = session.query(ExtractionHistory).order_by(
                    ExtractionHistory.extraction_time.desc()
                ).first()
                
                recent_extraction_info = {
                    'id': recent_extraction.id,
                    'datasource_id': recent_extraction.datasource_id,
                    'datasource_name': recent_extraction.datasource.name if recent_extraction.datasource else 'Unknown',
                    'extraction_time': recent_extraction.extraction_time.isoformat() if recent_extraction.extraction_time else None,
                    'status': recent_extraction.status,
                    'extracted_tables': recent_extraction.extracted_tables
                } if recent_extraction else None
                
                return jsonify({
                    'data_sources_count': data_sources_count,
                    'tables_count': tables_count,
                    'columns_count': columns_count,
                    'total_extracted_tables': total_size,
                    'recent_extraction': recent_extraction_info
                })
        except Exception as e:
            logging.error(f"获取概览数据失败: {str(e)}")
            return jsonify({'error': f'获取概览数据失败: {str(e)}'}), 500
    
    # 用户管理页面
    @app.route('/users')
    @login_required
    def users_page():
        """用户管理页面（管理员显示所有用户，普通用户显示个人信息）"""
        return render_template('users.html')
    
    # 用户管理API
    @app.route('/api/users', methods=['GET'])
    @admin_required
    def api_get_users():
        """获取所有用户"""
        try:
            users = get_all_users()
            return jsonify(users)
        except Exception as e:
            logging.error(f"获取用户列表失败: {str(e)}")
            return jsonify({'error': f'获取用户列表失败: {str(e)}'}), 500
    
    @app.route('/api/users/<int:user_id>', methods=['GET'])
    @admin_required
    def api_get_user(user_id):
        """获取单个用户"""
        try:
            user = get_user_by_id(user_id)
            if user:
                return jsonify(user.to_dict())
            return jsonify({'error': '用户不存在'}), 404
        except Exception as e:
            logging.error(f"获取用户失败: {str(e)}")
            return jsonify({'error': f'获取用户失败: {str(e)}'}), 500
    
    @app.route('/api/users', methods=['POST'])
    @admin_required
    def api_create_user():
        """创建用户"""
        try:
            data = request.json
            
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'缺少必需字段: {field}'}), 400
            
            success, message = create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                full_name=data.get('full_name'),
                role=data.get('role', 'user')
            )
            
            if success:
                return jsonify({'message': message}), 201
            return jsonify({'error': message}), 400
        except Exception as e:
            logging.error(f"创建用户失败: {str(e)}")
            return jsonify({'error': f'创建用户失败: {str(e)}'}), 500
    
    @app.route('/api/users/<int:user_id>', methods=['PUT'])
    @login_required
    def api_update_user(user_id):
        """更新用户（管理员可修改所有用户，普通用户只能修改自己）"""
        try:
            # 检查权限
            if session.get('role') != 'admin':
                # 普通用户只能修改自己的信息
                if session.get('user_id') != user_id:
                    return jsonify({'error': '无权修改其他用户信息', 'error_code': 'INSUFFICIENT_PERMISSIONS'}), 403

                # 普通用户只能修改email和full_name
                data = request.json
                allowed_fields = {'email', 'full_name'}
                update_data = {k: v for k, v in data.items() if k in allowed_fields}
            else:
                # 管理员可以修改所有字段
                update_data = request.json

            success, message = update_user(user_id, **update_data)

            if success:
                return jsonify({'message': message})
            return jsonify({'error': message}), 400
        except Exception as e:
            logging.error(f"更新用户失败: {str(e)}")
            return jsonify({'error': f'更新用户失败: {str(e)}'}), 500

    @app.route('/api/change-password', methods=['POST'])
    @login_required
    def api_change_password():
        """修改密码"""
        try:
            data = request.json
            current_password = data.get('current_password')
            new_password = data.get('new_password')

            if not current_password or not new_password:
                return jsonify({'error': '当前密码和新密码不能为空'}), 400

            user_id = session.get('user_id')
            success, message = change_user_password(user_id, current_password, new_password)

            if success:
                return jsonify({'message': message})
            return jsonify({'error': message}), 400
        except Exception as e:
            logging.error(f"修改密码失败: {str(e)}")
            return jsonify({'error': f'修改密码失败: {str(e)}'}), 500
    
    @app.route('/api/users/<int:user_id>', methods=['DELETE'])
    @admin_required
    def api_delete_user(user_id):
        """删除用户"""
        try:
            # 不允许删除自己
            if session.get('user_id') == user_id:
                return jsonify({'error': '不能删除自己的账户'}), 400
            
            success, message = delete_user(user_id)
            
            if success:
                return jsonify({'message': message})
            return jsonify({'error': message}), 400
        except Exception as e:
            logging.error(f"删除用户失败: {str(e)}")
            return jsonify({'error': f'删除用户失败: {str(e)}'}), 500
    
    @app.route('/login', methods=['GET'])
    def login_page():
        """登录页面"""
        return render_template('login.html')
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        """用户登录API"""
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': '用户名和密码不能为空'}), 400
            
            success, user_data, error_msg = login_user(username, password)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'user': user_data
                })
            else:
                return jsonify({'success': False, 'error': error_msg}), 401
        except Exception as e:
            logging.error(f"登录失败: {str(e)}")
            return jsonify({'success': False, 'error': f'登录失败: {str(e)}'}), 500
    
    @app.route('/api/logout', methods=['POST'])
    @login_required
    def api_logout():
        """用户登出API"""
        try:
            logout_user()
            return jsonify({'message': '登出成功'})
        except Exception as e:
            logging.error(f"登出失败: {str(e)}")
            return jsonify({'error': f'登出失败: {str(e)}'}), 500
    
    @app.route('/api/current-user', methods=['GET'])
    @login_required
    def get_current_user_info():
        """获取当前用户信息"""
        try:
            user = get_current_user()
            if user:
                return jsonify(user.to_dict())
            else:
                return jsonify({'error': '用户未登录'}), 401
        except Exception as e:
            logging.error(f"获取当前用户信息失败: {str(e)}")
            return jsonify({'error': f'获取当前用户信息失败: {str(e)}'}), 500
    
    @app.route('/api/check-permission', methods=['POST'])
    @login_required
    def check_permission():
        """检查用户权限"""
        try:
            data = request.json
            permission = data.get('permission')
            
            if not permission:
                return jsonify({'error': '权限名称不能为空'}), 400
            
            has_perm = has_permission(permission)
            return jsonify({'has_permission': has_perm})
        except Exception as e:
            logging.error(f"检查权限失败: {str(e)}")
            return jsonify({'error': f'检查权限失败: {str(e)}'}), 500
    
    @app.route('/')
    def index():
        """主页"""
        # 检查是否登录，如果未登录则重定向到登录页
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        """仪表板页面，显示资源概览"""
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('dashboard.html')
    
    @app.route('/data-sources')
    def data_sources():
        """数据源管理页面"""
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('data_sources.html')
    
    @app.route('/metadata')
    def metadata():
        """元数据浏览页面"""
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('metadata.html')
    
    @app.route('/table/<int:table_id>')
    def table_details(table_id):
        """表详情页面"""
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('table_details.html', table_id=table_id)
    
    @app.route('/history')
    def history():
        """抽取历史页面"""
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('history.html')
    
    @app.route('/etl')
    def etl():
        """ETL任务管理页面"""
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('etl.html')

    return app