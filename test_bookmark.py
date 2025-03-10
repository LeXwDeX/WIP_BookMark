import os
import json
from services.bookmark_service import BookmarkService
from modules.bookmark_analyzer import analyze_bookmarks
from modules.db_manager import BookmarkDBManager

def test_bookmark_sync():
    # 初始化BookmarkService
    service = BookmarkService('test_bookmarks.db')
    html_file = "favorites_2025_2_14.html"
    
    try:
        # 测试场景1：只比较标题
        print("\n=== 测试场景1：只比较标题 ===")
        stats = service.sync_bookmarks(html_file)
        print("同步结果:")
        print(f"- 新书签总数: {stats['total_new']}")
        print(f"- 添加书签数: {stats['added']}")
        print(f"- 更新书签数: {stats['updated']}")
        print(f"- 删除书签数: {stats['deleted']}")
        
        # 测试场景2：只比较URL
        print("\n=== 测试场景2：只比较URL ===")
        stats = service.sync_bookmarks(html_file, compare_fields=['url'])
        print("同步结果:")
        print(f"- 新书签总数: {stats['total_new']}")
        print(f"- 现有书签数: {stats['total_existing']}")
        print(f"- 更新书签数: {stats['updated']}")
        print(f"- 删除书签数: {stats['deleted']}")
        
        # 测试场景3：同时比较标题和URL
        print("\n=== 测试场景3：同时比较标题和URL ===")
        stats = service.sync_bookmarks(html_file, compare_fields=['title', 'url'])
        print("同步结果:")
        print(f"- 新书签总数: {stats['total_new']}")
        print(f"- 现有书签数: {stats['total_existing']}")
        print(f"- 更新书签数: {stats['updated']}")
        print(f"- 删除书签数: {stats['deleted']}")
        
        # 验证数据库中的书签
        bookmarks = json.loads(service.db_manager.export_bookmarks())
        print(f"\n数据库中的书签总数: {len(bookmarks)}")
        
        print("\n测试完成！")
        
    except Exception as e:
        print("测试失败:", e)
    finally:
        # 确保关闭数据库连接
        service.db_manager = None
        # 清理测试数据库
        if os.path.exists('test_bookmarks.db'):
            try:
                os.remove('test_bookmarks.db')
            except PermissionError:
                print("注意：无法删除测试数据库文件，可能需要手动删除。")

if __name__ == "__main__":
    test_bookmark_sync()