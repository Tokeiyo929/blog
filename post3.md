# LocalCache使用说明文档

LocalCache是一个用于本地数据缓存与读取的静态工具类,基于Unity的PlayerPrefFs,支持用户级(Local)与全局级(Global)的数据存储。

---

## 功能简介
- 对比 PlayerPrefs进行封装,优化访问性能,减少了GC。
- 提供对int、float、string类型的本地数据读写接口。
- 支持用户级和全局级键值分离。
- 提供本地缓存写入、读取、检测和删除功能。
- 支持将内存中缓存的值批量刷新到本地存储。

---

## 使用场景
适用于以下场景:
- 存储用户设定(如音量、分辨率、用户名)。
- 缓存玩家进度或偏好设置。
- 记录全局状态或配置(如首次启动标记、默认语言)。
- 支持在无权限写入PlayerPrefs时先写入内存缓存。

---

## 使用方式

### 写入本地数据
```csharp
LocalCache.SetLocalString("username","张三");
LocalCache.SetLocalint("level", 10);
LocalCache.SetLocalFloat("volume", 0.5f);
```

### 读取本地数据
```csharp
var name = LocalCache.GetLocalstring("username","默认用户名");
var level = LocalCache.GetLocalint("level", 1);
var volume = LocalCache.GetLocalFloat("volume");
```

### 检查本地键是否存在
```csharp
if (LocalCache.HasLocalKey("username"))
    // 键存在
```

### 删除本地键
```csharp
LocalCache.DeleteLocalkey("username");
```

---

## 全局数据操作
不依赖用户前缀,适合全局设定或设备级存储。

```csharp
LocalCache.SetGlobalString("language", "zh-CN");
var lang = LocalCache.GetGlobalString("language", "en");
LocalCache.DeleteGlobalKey("language");
```

---

## 刷新缓存到本地
将当前保存在内存中的值写入本地存储:

```csharp
LocalCache.FlushCache();
```

适用于在离线、权限限制等场景下的缓存同步。

```csharp
using UnityEngine;
using System.Collections.Generic;

public static class LocalCache
{
    private static Dictionary<string, string> _strDict = new Dictionary<string, string>();
    private static Dictionary<string, int> _intDict = new Dictionary<string, int>();
    private static Dictionary<string, float> _floatDict = new Dictionary<string, float>();
    private static Dictionary<string, bool> _keyDict = new Dictionary<string, bool>();

    public static string userKeyPrefix = string.Empty;
    public static string globalKeyPrefix = "";
    private static LRUCache<(string, string), string> keyCache = new LRUCache<(string, string), string>(64);
    private static bool _CheckPermission()
    {
        return true;
    }

    public static void FlushCache()
    {
        if (!_CheckPermission())
        {
            return;
        }

        foreach (var pairs in _strDict)
        {
            PlayerPrefs.SetString(pairs.Key, pairs.Value);
        }
        foreach (var pairs in _intDict)
        {
            PlayerPrefs.SetInt(pairs.Key, pairs.Value);
        }
        foreach (var pairs in _floatDict)
        {
            PlayerPrefs.SetFloat(pairs.Key, pairs.Value);
        }
    }
    private static string _GetCacheKey(string prefix, string key)
    {
        var tmpKey = (prefix, key);
        var fixedKey = keyCache.Get(tmpKey);
        if (string.IsNullOrEmpty(fixedKey))
        {
            fixedKey = string.Format("{0}_{1}", prefix, key);
            keyCache.Set(tmpKey, fixedKey);
        }

        return fixedKey;
    }

    private static string _GetUserKey(string key)
    {
        return _GetCacheKey(userKeyPrefix, key);
    }

    public static bool HasLocalKey(string key)
    {
        if (!_CheckPermission())
        {
            return _keyDict.ContainsKey(_GetUserKey(key));
        }
        return PlayerPrefs.HasKey(_GetUserKey(key));
    }

    public static void DeleteLocalKey(string key)
    {
        PlayerPrefs.DeleteKey(_GetUserKey(key));
    }

    public static bool HasGlobalKey(string key)
    {
        if (!_CheckPermission())
        {
            return _keyDict.ContainsKey(_GetGlobalKey(key));
        }
        return PlayerPrefs.HasKey(_GetGlobalKey(key));
    }

    public static void DeleteGlobalKey(string key)
    {
        PlayerPrefs.DeleteKey(_GetGlobalKey(key));
    }

    /// <summary>
    /// 用户绑定,
    /// </summary>
    /// <param name="key"></param>
    /// <param name="defaultVal"></param>
    /// <returns></returns>
    public static int GetLocalInt(string key, int defaultVal = 0)
    {
        key = _GetUserKey(key);
        if (!_CheckPermission())
        {
            if (_intDict.TryGetValue(key,out var result))
            {
                return result;
            }
            return defaultVal;
        }
        return PlayerPrefs.GetInt(key, defaultVal);
    }

    public static float GetLocalFloat(string key)
    {
        key = _GetUserKey(key);
        if (!_CheckPermission())
        {
            if (_floatDict.TryGetValue(key, out var result))
            {
                return result;
            }
            return 0f;
        }
        return PlayerPrefs.GetFloat(key, 0f);
    }

    public static string GetLocalString(string key, string defaultVal = "")
    {
        key = _GetUserKey(key);
        if (!_CheckPermission())
        {
            if (_strDict.TryGetValue(key, out var result))
            {
                return result;
            }
            return defaultVal;
        }
        return PlayerPrefs.GetString(key, defaultVal);
    }

    public static void SetLocalString(string key, string val)
    {
        key = _GetUserKey(key);
        if (!_CheckPermission())
        {
            _strDict[key] = val;
            _keyDict[key] = true;
            return;
        }
        PlayerPrefs.SetString(key, val);
    }

    public static void SetLocalInt(string key, int val)
    {
        key = _GetUserKey(key);
        if (!_CheckPermission())
        {
            _intDict[key] = val;
            _keyDict[key] = true;
            return;
        }
        PlayerPrefs.SetInt(key, val);
    }

    public static void SetLocalFloat(string key, float val)
    {
        key = _GetUserKey(key);
        if (!_CheckPermission())
        {
            _floatDict[key] = val;
            _keyDict[key] = true;
            return;
        }
        PlayerPrefs.SetFloat(key, val);
    }

    private static string _GetGlobalKey(string key)
    {
        return _GetCacheKey(globalKeyPrefix, key);
    }

    public static void SetGlobalString(string key, string val)
    {
        key = _GetGlobalKey(key);

        if (!_CheckPermission())
        {
            _strDict[key] = val;
            _keyDict[key] = true;
            return;
        }
        PlayerPrefs.SetString(key, val);
    }

    /// <summary>
    /// 全局绑定,与用户ID无关.
    /// </summary>
    /// <param name="key"></param>
    /// <param name="defaultVal"></param>
    /// <returns></returns>
    public static string GetGlobalString(string key, string defaultVal = "")
    {
        key = _GetGlobalKey(key);

        if (!_CheckPermission())
        {
            if (_strDict.TryGetValue(key, out var result))
            {
                return result;
            }
            return defaultVal;
        }
        return PlayerPrefs.GetString(key, defaultVal);
    }

    public static int GetGlobalInt(string key, int defaultVal = 0)
    {
        key = _GetGlobalKey(key);
        if (!_CheckPermission())
        {
            if (_intDict.TryGetValue(key, out var result))
            {
                return result;
            }
            return defaultVal;
        }
        return PlayerPrefs.GetInt(key, defaultVal);
    }

    public static void SetGlobalInt(string key, int val)
    {
        key = _GetGlobalKey(key);
        if (!_CheckPermission())
        {
            _intDict[key] = val;
            _keyDict[key] = true;
            return;
        }
        PlayerPrefs.SetInt(key, val);
    }
}
```

```csharp
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.Pool; //引入对象池 (JasonLee)

/// <summary>
/// 基于 UnityEngine.Pool.ObjectPool 的 LRU 缓存容器(JasonLee)
/// </summary>
public class LRUCache<T,DATA>:IEnumerable<DATA>,IDisposable
{
    /// <summary>
    /// 双向链表节点结构(Jason Lee)
    /// </summary>
    public class ListNode<T2,DATA2>
    {
        public ListNode<T2,DATA2> Prev;
        public ListNode<T2,DATA2> Next;
        public DATA2 Value;
        public T2 Key;
        public ListNode(T2 key, DATA2 val)
        {
            Value = val;
            Key = key;
            this.Prev = null;
            this.Next = null;
        }
        //用于池化回收时的字段清空(JasonLee)
        public void Reset()
        {
            Prev = null;
            Next = null;
            Key = default;
            Value = default;
        }
    }

    private int _size;//链表长度
    private int _capacity;//缓存容量 
    
    //初始化字典时应设置容量，避免多次扩容引发 GC(JasonLee)
    private Dictionary<T, ListNode<T,DATA>> _dic;//key +缓存数据
	public IReadOnlyCollection<T> Keys => _dic.Keys;
    private ListNode<T,DATA> _linkHead;// 作为一个哨兵节点，简化链表操作
    // 用于存储回收的 ListNode 对象池(JasonLee)
    private ObjectPool<ListNode<T, DATA>> _nodePool;
    private System.Action<T, DATA> OnRemoveCall;
    public LRUCache(int capacity,System.Action<T,DATA> OnRemoveCall = null)
    {
        _linkHead = new ListNode<T,DATA>(default(T), default(DATA));
        _linkHead.Next = _linkHead.Prev = _linkHead;
        this._size = 0;
        this._capacity = capacity;
        this._dic = new Dictionary<T, ListNode<T,DATA>>(_capacity);//初始化 Dictionary 时设置容量，避免哈希表扩容引发 GC(JasonLee)        
        this.OnRemoveCall = OnRemoveCall;
        //初始化 Unity 对象池，带 OnRelease 清理逻辑，最大容量设置为 2 倍(JasonLee)
        _nodePool = new ObjectPool<ListNode<T, DATA>>(
            createFunc: () => new ListNode<T, DATA>(default, default),
            actionOnGet: null,
            actionOnRelease: n => n.Reset(),
            collectionCheck: true,
            defaultCapacity: capacity,
            maxSize: capacity * 2
        );
    }

    public int Count=> _size;

    /// <summary>
    /// 方便处理值类型
    /// </summary>
    /// <param name="key"></param>
    /// <param name="value"></param>
    /// <returns></returns>
    public bool TryGet(T key,out DATA value)
    {
        if (_dic.TryGetValue(key, out var listNode))
        {
            MoveToHead(listNode);
            value = listNode.Value;
            return true;
        }

        value= default(DATA);
        return false;
    }

    public DATA Get(T key)
    {
        if (_dic.TryGetValue(key, out var listNode))
        {
            MoveToHead(listNode);
            return listNode.Value;
        }
        return default(DATA);
    }

    /// <summary>
    /// 原返回值并无应用，且没有相应的资源释放，此处改为void，并添加内存回收（JasonLee）
    /// </summary>
    /// <param name="key"></param>
    public void Remove(T key)
    {
        if (!_dic.TryGetValue(key, out var node))//添加out逻辑(JasonLee)
        {
            return;
        }
        else
        {
            //ListNode<T, DATA> n = _dic[key];//避免重新分配内存指针(JasonLee)
            RemoveFromList(node);
            _dic.Remove(key);
            _size--;
            OnRemoveCall?.Invoke(node.Key, node.Value);//补充遗漏回调逻辑(JasonLee)
            RecycleNode(node); //释放 ListNode 对象，放入池中复用(JasonLee)            
        }
    }

    public void Set(T key, DATA value)
    {
        ListNode<T,DATA> n;
        if (_dic.TryGetValue(key, out var listNode))
        {
            n = listNode;
            n.Value = value;
            MoveToHead(n);
        }
        else
        {
            //n = new ListNode<T,DATA>(key, value);
            n = GetOrCreateNode(key, value);//替代 new，使用池获取或创建(JasonLee)
            AttachToHead(n);
            _size++;
            _dic.Add(key, n);
        }
        if (_size > _capacity)
        {
            //内部须池化节点（JasonLee）
            RemoveLast();// 如果更新节点后超出容量，删除最后一个 ,removeLast中做了size--操作
        }
    }

    public bool IsFull()
    {
        return _dic.Count == _capacity;
    }

    //改动较多，重写Clear方法（JasonLee）
    public void Clear()
    {
        var node = _linkHead.Next;
        while (node != _linkHead) // 避免 foreach 带来的 GC 分配，并精确操作链表（JasonLee）
        {
            var next = node.Next; // 回收前缓存 Next，避免 RecycleNode 清空后断链（JasonLee）

            OnRemoveCall?.Invoke(node.Key, node.Value); 
            RecycleNode(node); // 将节点归还对象池，释放内存引用，支持复用（JasonLee）
            node = next;
        }

        _linkHead.Next = _linkHead.Prev = _linkHead;
        _dic.Clear();
        _size = 0;
    }

    public void Dispose()
    {
        Clear();
        OnRemoveCall = null;
        _nodePool.Clear();//Unity 对象池清空（彻底释放）
    }

    // 移出链表最后一个节点
    //自己检测,
    public T PopLast(out DATA data)
    {
        ListNode<T, DATA> deNode = _linkHead.Prev;
        if(deNode == null || _linkHead == deNode)
        {
            throw new InvalidOperationException("Check Before PopLast");
        }
        RemoveFromList(deNode);
        _dic.Remove(deNode.Key);
        _size--;
        var key = deNode.Key;
        data = deNode.Value;
        OnRemoveCall?.Invoke(key, data);
        RecycleNode(deNode); //放入对象池（JasonLee）
        return key;
    }

    public bool TryLast(out T key, out DATA data)
    {
        ListNode<T, DATA> deNode = _linkHead.Prev;
        if (deNode == null || _linkHead == deNode)
        {
            key = default(T);
            data = default(DATA);
            return false;
        }

        key = deNode.Key;
        data = deNode.Value;
        return true;
    }

    // 移出链表最后一个节点
    private void RemoveLast()
    {
        ListNode<T,DATA> deNode = _linkHead.Prev;
        RemoveFromList(deNode);
        _dic.Remove(deNode.Key);
        _size--;
        OnRemoveCall?.Invoke(deNode.Key, deNode.Value);
        RecycleNode(deNode); //放入对象池（JasonLee）
    }

    // 将一个孤立节点放到头部
    private void AttachToHead(ListNode<T,DATA> n)
    {
        n.Prev = _linkHead;
        n.Next = _linkHead.Next;
        _linkHead.Next.Prev = n;
        _linkHead.Next = n;
    }

    // 将一个链表中的节点放到头部
    private void MoveToHead(ListNode<T,DATA> n)
    {
        RemoveFromList(n);
        AttachToHead(n);
    }
    private void RemoveFromList(ListNode<T,DATA> n)
    {
        //将该节点从链表删除
        n.Prev.Next = n.Next;
        n.Next.Prev = n.Prev;

        n.Prev = null; //清理引用避免悬挂(JasonLee)
        n.Next = null;
    }

    /// <summary>
    /// 从 Unity 对象池中获取新节点或复用节点(JasonLee)
    /// </summary>
    private ListNode<T, DATA> GetOrCreateNode(T key, DATA value)
    {
        var node = _nodePool.Get(); //Unity 内置池中取对象
        node.Key = key;
        node.Value = value;
        return node;
    }

    /// <summary>
    /// 回收节点到 Unity 对象池(JasonLee)
    /// </summary>
    private void RecycleNode(ListNode<T, DATA> node)
    {
        _nodePool.Release(node); // 调用 OnRelease 自动 Reset
    }
    public Enumerator GetEnumerator()
    {
        return new Enumerator(_dic.Values);
    }

    IEnumerator IEnumerable.GetEnumerator()
    {
        return this.GetEnumerator();
    }
    IEnumerator<DATA> IEnumerable<DATA>.GetEnumerator()
    {
        return this.GetEnumerator();
    }

    public struct Enumerator : IEnumerator<DATA>, IDisposable, IEnumerator
    {
        public DATA Current => temp.Current.Value;
        object IEnumerator.Current => temp.Current.Value;

        private Dictionary<T, ListNode<T, DATA>>.ValueCollection.Enumerator temp;
        public Enumerator(Dictionary<T, ListNode<T,DATA>>.ValueCollection temp)
        {
            this.temp = temp.GetEnumerator();
        }
        public void Dispose()
        {
            temp.Dispose();
        }
        public bool MoveNext()
        {
            return temp.MoveNext();
        }
        public void Reset()
        {
            this.temp = default(Dictionary<T, ListNode<T, DATA>>.ValueCollection.Enumerator);
        }
    }
}
```

