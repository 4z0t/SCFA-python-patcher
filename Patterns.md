During REing you will notice certain patterns. 

## Object ctor and dtor

These patterns will help with noticing certain structures when REing code.

### std::vector

In ctor you won't notice it at first glance. However if you look closely:

```cpp
...
*(_DWORD *)(a + 1) = 0;
*(_DWORD *)(a + 2) = 0;
*(_DWORD *)(a + 3) = 0;
...
```
You'll notice that `*a` wasn't set to anything, and if you find dtor:
```cpp
...
if(*(a + 1))
{
    ...
    free(*(_DWORD *)(a + 1)); // or operator delete(*(a + 1));
}
*(_DWORD *)(a + 1) = 0;
*(_DWORD *)(a + 2) = 0;
*(_DWORD *)(a + 3) = 0;
...
```
This is a definitely std::vector and function before free (if it presents) may suggest you the type of vector.

```cpp
...
if(a->v.begin)
{
    ...
    free(a->v.begin); // or operator delete(*(a + 1));
}
a->v.begin = 0;
a->v.end = 0;
a->v.capacity_end = 0;
...
```

**Note: offsets may be different, but overall idea stays**

An example:

```cpp
 v2 = *(std::string **)(a1 + 8);
  if ( v2 )
  {
    func_FreeStringsRange(v2, *(std::string **)(a1 + 12));
    operator delete(*(void **)(a1 + 8));
  }
  *(_DWORD *)(a1 + 8) = 0;
  *(_DWORD *)(a1 + 12) = 0;
  *(_DWORD *)(a1 + 16) = 0;
```

This is a vector of std::string.

### linked list

ctor
```cpp
*(_DWORD *)(a1 + 4) = a1 + 4;
*(_DWORD *)(a1 + 8) = a1 + 4;
```

dtor
```cpp
*(_DWORD *)(*(_DWORD *)(a1 + 4) + 4) = *(_DWORD *)(a1 + 8);
**(_DWORD **)(a1 + 8) = *(_DWORD *)(a1 + 4);
*(_DWORD *)(a1 + 4) = a1 + 4;
*(_DWORD *)(a1 + 8) = a1 + 4;
```

This is a linked list

```cpp
a1->l.prev = &a1->l;
a1->l.next = &a1->l;
```

```cpp
  a1->l.next->prev = a1->l.prev;
  a1->l.prev->next = a1->l.next;
  a1->l.prev = &a1->l;
  a1->l.next = &a1->l;
```

### std::map (binary tree)

```cpp
v1 = sub_465480();                                              // this function has weird stuff and call to *new* with size we'll use later
                                                                // no first field set
*((_DWORD *)this + 1) = v1;                                     // doing some stuff with the second field
*(_BYTE *)(v1 + 45/*any offset*/) = 1;                          // setting some value to 1
*(_DWORD *)(*((_DWORD *)this + 1) + 4) = *((_DWORD *)this + 1);  
**((_DWORD **)this + 1) = *((_DWORD *)this + 1);
*(_DWORD *)(*((_DWORD *)this + 1) + 8) = *((_DWORD *)this + 1); 
*((_DWORD *)this + 2) = 0;                                      // setting third field to zero
```

This is a map based on binary tree. 

```cpp
node = create_node();
this->m.root = node;
node->is_leaf = 1;
this->m.root->parent = this->m.root;
this->m.root->left = this->m.root;
this->m.root->right = this->m.root;
this->m.size = 0;
```

Where dtor will look very fancy and you'll guess it very fast

```cpp
... // maybe an iteration over map before
some_function(&this->m, &node, this->m.root->left, this->m.root);
operator delete(this->m.root);
this->m.root = 0;
this->m.size = 0;
...
```

### std::shared_ptr

```cpp
if ( v10 )
{
  if ( !_InterlockedExchangeAdd(v10 + 1, 0xFFFFFFFF) )
  {
    (*(void (__thiscall **)(volatile signed __int32 *))(*v10 + 4))(v10);
    if ( !_InterlockedExchangeAdd(v10 + 2, 0xFFFFFFFF) )
      (*(void (__thiscall **)(volatile signed __int32 *))(*v10 + 8))(v10);
  }
}
```
You'll see this very frequently. It is inlined dtor of shared pointer. So if `v10` is a counter block, then field before it is pointer to data associated with it.

```cpp
if ( pi )
  {
    if ( !_InterlockedExchangeAdd(&pi->use_count_, 0xFFFFFFFF) )
    {
      pi->vtable->dispose(pi);
      if ( !_InterlockedExchangeAdd(&pi->weak_count_, 0xFFFFFFFF) )
        pi->vtable->destroy(pi);
    }
  }
```