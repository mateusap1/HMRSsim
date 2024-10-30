#include <iostream>
#include <string>

#include <behaviortree_cpp_v3/behavior_tree.h>
#include <behaviortree_cpp_v3/bt_factory.h>
#include <behaviortree_cpp_v3/blackboard.h>

class MoveToNurse : public BT::SyncActionNode
{
public:
    MoveToNurse(const std::string &name) : BT::SyncActionNode(name, {}) {}

    BT::NodeStatus tick() override
    {
        std::cout << "Moving to nurse... " << std::endl;
        return BT::NodeStatus::SUCCESS;
    }
};

class ReceiveBarcode : public BT::SyncActionNode
{
public:
    ReceiveBarcode(const std::string &name, const BT::NodeConfiguration &config) : BT::SyncActionNode(name, config) {}

    static BT::PortsList providedPorts()
    {
        return {BT::OutputPort<std::string>("barcode")};
    }

    BT::NodeStatus tick() override
    {
        std::string barcode_key;

        std::cout << "Barcode key: ";
        std::cin >> barcode_key;

        setOutput("barcode", barcode_key);

        std::cout << "Setting key to " << barcode_key << std::endl;
        return BT::NodeStatus::SUCCESS;
    }
};

class CheckBarcode : public BT::ConditionNode
{
public:
    CheckBarcode(const std::string &name, const BT::NodeConfiguration &config) : BT::ConditionNode(name, config) {}

    static BT::PortsList providedPorts()
    {
        return {BT::InputPort<std::string>("barcode")};
    }

    BT::NodeStatus tick() override
    {
        BT::Optional<std::string> key = getInput<std::string>("barcode");

        if (!key)
        {
            throw BT::RuntimeError("missing required input [message]: ", key.error());
        }

        if (key.value() != "test_key")
        {
            std::cout << "Nurse auth failed with " << key.value() << std::endl;
            return BT::NodeStatus::FAILURE;
        }

        std::cout << "Nurse authenticated!" << std::endl;
        return BT::NodeStatus::SUCCESS;
    }
};

class ReleaseDrawer : public BT::SyncActionNode
{
public:
    ReleaseDrawer(const std::string &name) : BT::SyncActionNode(name, {}) {}

    BT::NodeStatus tick() override
    {
        std::cout << "Releasing drawer... " << this->name() << std::endl;
        return BT::NodeStatus::SUCCESS;
    }
};

class WaitDrawerClose : public BT::ConditionNode
{
public:
    WaitDrawerClose(const std::string &name) : BT::ConditionNode(name, {}) {}

    BT::NodeStatus tick() override
    {
        std::getchar();

        std::cout << "User closed drawer " << this->name() << std::endl;
        return BT::NodeStatus::SUCCESS;
    }
};

class MoveToLab : public BT::SyncActionNode
{
public:
    MoveToLab(const std::string &name) : BT::SyncActionNode(name, {}) {}

    BT::NodeStatus tick() override
    {
        std::cout << "Moving to lab... " << this->name() << std::endl;
        return BT::NodeStatus::SUCCESS;
    }
};

class MoveToInitial : public BT::SyncActionNode
{
public:
    MoveToInitial(const std::string &name) : BT::SyncActionNode(name, {}) {}

    BT::NodeStatus tick() override
    {
        std::cout << "Moving to initial... " << this->name() << std::endl;
        return BT::NodeStatus::SUCCESS;
    }
};
