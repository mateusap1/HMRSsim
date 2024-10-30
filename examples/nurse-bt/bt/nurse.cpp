#include "behaviortree_cpp_v3/bt_factory.h"

#include "nodes.cpp"

using namespace BT;

int main()
{
  // We use the BehaviorTreeFactory to register our custom nodes
  BehaviorTreeFactory factory;

  // The recommended way to create a Node is through inheritance.
  factory.registerNodeType<MoveToNurse>("MoveToNurse");
  factory.registerNodeType<ReceiveBarcode>("ReceiveBarcode");
  factory.registerNodeType<CheckBarcode>("CheckBarcode");
  factory.registerNodeType<ReleaseDrawer>("ReleaseDrawer");
  factory.registerNodeType<WaitDrawerClose>("WaitDrawerClose");
  factory.registerNodeType<MoveToLab>("MoveToLab");
  factory.registerNodeType<MoveToInitial>("MoveToInitial");

  // IMPORTANT: when the object "tree" goes out of scope, all the
  // TreeNodes are destroyed
  auto tree = factory.createTreeFromFile("./tree.xml");

  // To "execute" a Tree you need to "tick" it.
  // The tick is propagated to the children based on the logic of the tree.
  // In this case, the entire sequence is executed, because all the children
  // of the Sequence return SUCCESS.
  tree.tickRootWhileRunning();

  return 0;
}
