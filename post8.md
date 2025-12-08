---
title: 代码编写规范​
category: [代码解析]
date: 2025-12-03
cover_image: https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=1170&q=80
excerpt: 本文讨论了 prefab 中特效的处理方式，旨在解决特效嵌入 prefab 导致的资源卸载困难和纹理资源冗余问题，同时统一制作方式并减少程序接入。
tags: [美术, 程序]
---

代码编写规范​

# 1.前言​


1.方便代码的交流和维护。​
2.不影响编码的效率，不与大众习惯冲突。​
3.使代码更美观、阅读更方便。​
4.使代码的逻辑更清晰、更易于理解。​
本套编码规范是对程序员编写高质量、高可维护性能的编码的规范化文档，本文档所有编码规范中除打印输出以及字符串变量内容以外，不允许出现任何中文、拼音等标识符。​
切记Debug.LogError打印的测试日志提交时无必要请删除。​

# 2.注释要求​

类型、属性、事件、方法、方法参数，根据需要添加注释。 ​
如果类型、属性、事件、方法、方法参数的名称已经是自解释了，不需要加注释；​
否则需要添加注释。​

# 3.文件要求​

类名与源文件名一致。避免使用大文件，避免使用太长的方法。代码中使用相对路径，拒绝绝对路径。 ​
Prefab名字和脚本名字保持一致。​
非Editor代码要放到Scripts目录下，并按功能放到Scripts对应的子目录下.​

# 4.排版要求​

类型成员的排列顺序自上而下依次为： ​
字段：公有字段，、受保护字段（尽量不要使用公有字段）， 私有字段 ​
属性：公有属性，受保护属性， 私有属性 ​
事件：公有事件，受保护事件、私有事件、​
构造函数：参数数量最少的构造函数，参数数量中等的构造函数，参数数量最多的构造函数​
方法：重载方法的排列顺序与构造函数相同，从参数数量最少往下至参数最多​
静态变量，方法等靠前放​
​

# 5. 命名规范​


## 1. Pascal命名法：每个单词首字母均大写。​

Camel命名法：第一个单词首字母小写，其余单词首字母大写​

## 2. 所有非布尔类型的变量必须使用简短、清晰并且意义明确的名词作为变量名。​

所有非布尔类型的变量的大小写需要遵守Pascall规则。​

## 3.所有布尔类型变量需要遵守Pascal规则，但前面需要增加小写的加is/has/b 做前缀。​

例如: 用 bDead, 不要使用Dead.​
不要使用布尔变量保存复杂的，或者需要依赖其他属性的状态信息，这会让状态变得复杂和难以理解，如果需       要尽量使用枚举来代替。​

## 4.数组的命名规则通常和所包含的元素的规则一样，但注意要用复数。​


## 5.所有可以安全的更改数据内容的变量都需要被标记为public​

`相反，所有不能更改或者不能暴露给设计师的变量都需要标记为private，如果确实要暴露但又不想破 坏程序封装，这些变量就需要被标为[SerializedFeild]​`
`6.对于可编辑的变量，如果不适合直接输入具体数值，那么应该通过一个滑动条(Slider)并且加上取值范围来让策划输入。可以用[Range(min,max)]属性实现。​`

## 7.类​

命名中不要使用下划线及数字。​
UI相关的类，使用UI前缀 如界面相关的增加Window后缀如： public class UIUseItemWindow ；界面内子物体增加Cell后缀，如 UIMailCell ； 管理器类 增加Manager后缀，如：LoadingManager​

## 8.所有单词大写，多个单词之间用下划线（”_”）隔开，如：​

```csharp
public const int PAGE_INDEX = 6;​
```



## 9.命名空间。​

采用Pascal方式命名，一定不能使用简写，不能使用中文字符​

## 10.方法和参数。 ​

用动词或动词短语命名方法名，保证方法名清晰，尽量达到望文生义的境界采用Pascal方式命名，尽量少用或不用缩写，若使用了缩写一定要在注释中详细注明方法的用途。命名示例： ​

```csharp
object GetCache(string cacheKey)​
bool IsInt(string needCheckString)​
```



## 11.枚举。​

用短语命名枚举，采用Pascal方式，保证枚举名清晰，尽量达到望文生义的境界，住释中详细注明枚举的用途。枚举命名示例： ​

```csharp
public enum OrderFlag​
{​
None,​
First    //第一​
}​
```



## 12.单例模式​

1.命名使用_instance​
2.对应属性使用Instance​
3.静态取单例使用singleton前缀， 如  ​

```csharp
public static AmazonPaymentManager singletonAmazon()​
```



# 6.  委托(delegate)与事件（Event）​

1、用动词短语命名委托，保证委托名清晰，尽量达到望文生义的境界。​
2、采用Pascal方式命名，一定不能使用简写。如：​
委托与事件命名示例：​

```csharp
public delegate void OnMenuClick();​
public delegate void OnMenuClose(); ​
public event RaiseEventHandler RaiseEvent;​
```



# 7. Manager协议规范​

增加各个发送协议方法命名Send前缀 并增加注释​
协议返回命名Reply后缀 并增加注释 ​
比如​

```csharp
SendLockBuilding //发送建筑解锁​
LockBuildingReply //建筑解锁返回​
```

新增监听事件DataChangeType文件中增加注释​
协议发送添加  UILoadingView.ShowLoadingView();​
协议返回添加 UILoadingView.HideLoadingView();​

# 8.其他​

1.禁止在update或者timer中频繁GetComponent或者切割字符串​
2.类中Start函数或者Update函数无用的情况下请删除方法​
3.界面中调用Subscribe事件 请对应Unsubscribe​
4.TimerManager.Instance.addTimer 使用该方法的 要手动调用TimerManager.Instance.removeTimer​
5.transform.Find（）等find方法 能不使用就不使用，看到老代码了可以修改下​
6.提交资源和代码 请使用jira单号提交 如：Fixed issue # RG-123 美女系统​

# 9.命名规范汇总​

代码元素                命名风格                                 示例与说明​
类/结构体             Pascal Case                  public class FileStream​
接口                 Pascal Case，前缀 I                  public interface IEnumerable​
方法                 Pascal Case                       public void CalculateTotal()​
属性                 Pascal Case                    public string FirstName { get;set; } ​
变量                Camel Case     public string connStr / 私有private string  _connStr​
局部参数            Camel Case                  public void AddUser(string userId)​
常量        全大写，下划线分隔    public const int MAX_USERS = 100; / private const int _MAX_USERS = 100;​
静态变量             Pascal Case                public static int MaxUsers = 100; / private static int _MaxUsers​
枚举类型           Pascal Case                            public enum EFileMode​
枚举成员           Pascal Case                             FileMode.Read​
​代码编写规范​
​代码编写规范​
​代码编写规范​

---


